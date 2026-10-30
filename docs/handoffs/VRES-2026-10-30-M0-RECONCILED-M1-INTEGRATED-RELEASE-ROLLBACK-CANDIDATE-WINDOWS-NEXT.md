# Vres-OS — 2026-10-30 M0 reconciled / M1 PERSONAL offline integrated upgrade-and-rollback candidate

**Evidence:** Live GitHub source reviews and exact-parent, nonforce feature commit plus remote readback: DONE. New Windows tests, physical installation, actual installer, pip install, native Claude and database operations: NOT_RUN. Personal one-Windows-user program, NOT enterprise.

**Repository:** https://github.com/vosser24/Vres-OS
**Canonical docs:** docs/chatgpt-continuity-20261023. Prior verified docs HEAD 98127b10e73f3a373147d499fa3f8f0911e065cd, tree 921dba6575cedb47eade664fdc8cdead13e065d9. Reverify actual latest docs HEAD, then read current index FIRST in every chat.

## 1. Hard safety holds and history

- **LIVE_SCHEMA_048_INCIDENT=OPEN**. NO PostgreSQL even SELECT, direct or indirect through Vres CLI, MCP, bootstrap, doctor, hooks, test recovery, migrations, F2 or external clients. This handoff grants no separate test database.
- **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**. Seven historical native Claude Code Read/Grep posttool auto DB attempts refused. NO ordinary native Claude, installed Vres/Claude hooks/lifecycle, global or managed config, PRISM activation.
- No independent F1 positive issuer, protected Fable/high, real Chairman model switch, user-profile/credential/real legacy changes, product-main merge, PR, go-live, or unapproved installed release. P2 requires specific consent and rollback evidence; P3 STOP under the incidents.
- Preserve original rejected A12 345a568b551ac23183c54f10611335adee903b96 (18 PASS/1 FAIL, exit1) and A13 cdaa39aaa774cef88a4831bf6b157e380fbb69d9 (28 PASS/1 FAIL, exit1), corrected R1 outcomes, A16 env script-copy ambiguity, A19 blocked/uncommitted, PT1/PT2A–D, Hook-R1, #165, #168 A1–A18, Stage1–6, #176 E7/E8/C2B/R0/F2, V-01..V-42, all protected old worktrees. No rewritten failures.

## 2. M0 — verified GitHub source identities and compatibility

| Reference | HEAD / tree | Status |
| --- | --- | --- |
| Previous docs checkpoint | 98127b10e73f3a373147d499fa3f8f0911e065cd / 921dba6575cedb47eade664fdc8cdead13e065d9 | Live GitHub verified |
| Product main | 9a8acc5d464b96432a93cb95daa9581412fb07ee / 659d3fdd6e635dbaecbd5c492ba7279754edaec7 | GitHub verified, unchanged |
| Accepted A18 | 7bace7758e5c7f9a00f26179eb741ef3a319bc77 / 4d17344a9510de6394840092cf33729ab153fbb5 | Historical 49 selected Windows PASS, 33 pre/post blobs, env restored; not installed |
| Last observed installed P2 source | 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c / 205c081277ece483c634e1c801c39595abd4549c | LAST WINDOWS OBSERVATION, not freshly inspected |
| New M1 feature source | **28120eb49b6b950c7402455db19dcbdcf6d991a6 / 815fce697f16509bae150729891738d879d6ca9c** | GitHub remote and exact three-path compare verified; Windows NOT_RUN |

GitHub compares: main→P2 ahead22/behind0; P2→A18 ahead52/behind0; main→A18 ahead74/behind0, 111 paths; M1 direct one-commit child of A18. No current Windows installation observation may be inferred from GitHub.

Stage6 P2 hooks original Git blob 5833973d9be6ccf4263dda2d461cc5994d30416c; SHA256 700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7. Stage6 found installed/staged P2 match release manifest with five unchanged local hashes, NOT present-day re-verification. A18 source hook Git blob e286e4be47d058ee6ed6a3169fc45803aedc0df1, SHA256 88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2. Stage3 saw 9 installed Read/Glob/Grep posthook declarations versus A18 zero, not nine executions. Stage4 17 groups, three matcher-only differences, zero nonmatcher difference; Stage5 in-memory 9→0 correction; NOT installed. Stop repeating matcher diagnosis.

M0 inspected actual GitHub P2/A18 files:
- src/vres_os/release_inputs.py Git blob a0cdf3195f0cf0f2a61ce32521a74f78260832f7 unchanged P2→A18: only migration SQL 001–041 pinned by canonical text SHA256, greater than 041 and experimental C2B/R0/F2/C2A inputs rejected. This was source review, no runtime call, no database contact.
- src/vres_os/release_artifact.py blob ddfc1beacad98199b489dc6f56456baf4d519c6a unchanged P2→A18: pinned HEAD and Git object SHA-1, staged package/plugin/Windows scripts and release metadata, manifest SHA256, verification of package/plugin byte content. ZIP source refused, release scope excludes docs/tests. Git SHA is source binding NOT independent signature. pip dependencies are resolved at install time, not locked; full pip installation still NOT_RUN.
- install.ps1 blob 29a5f0da235021cc8c5607eb92218e5ea98145fa unchanged P2→A18, update.ps1 shares it. Actual installer can invoke Claude version/plugin list/validate, winget PostgreSQL installation, pip, user-profile changes and database-skipped doctor. **NEVER RUN it with host/DB incidents open**; absence of explicit database command is not proof third-party subprocesses have no contact.
- src/vres_os/install_recovery.py original P2/A18 blob 1c0d585645280678af4875f2842a3350f9805e0a: v2 snapshot, preinstall Claude file/launcher/plugin tree digest, journal/inspect/recover confirm flow and fail-closed checks. **Found substantive gap:** if the previous managed plugin had already been moved to its backup, recovery verified only its Vres marker; it did NOT verify backup bytes against original preinstall snapshot digest. A corrupted P2 hook backup could be restored. Distinct from no-backup branch already verified by digest.
- Chairman plugin is still Sonnet/high; Opus/medium is source-only candidate. task_lifecycle/session_lifecycle import database access and must NOT be executed; project_adoption.py includes scoped static review but real project held; credential_broker/local_secrets provide source functions but vault access and real linking not exercised. database_targets.py is a guard, not permission to contact schema-048 target.

**M0 decision:** keep intact A18 source and pinned release infrastructure; fix one justified v2 rollback identity gap, deliver ONE integrated Git-object stage and synthetic install/rollback rehearsal. No A19/A20 serial micro-gates, Stage7, hotpatch, enterprise IAM or new release framework.

## 3. M1 feature commit and exact files

Branch: feature/personal-m1-integrated-upgrade-rollback-20261030
Commit: **28120eb49b6b950c7402455db19dcbdcf6d991a6**
Tree: **815fce697f16509bae150729891738d879d6ca9c**
Only parent: A18 7bace7758e5c7f9a00f26179eb741ef3a319bc77
Link: https://github.com/vosser24/Vres-OS/commit/28120eb49b6b950c7402455db19dcbdcf6d991a6

Exactly these paths changed, verified by GitHub compare and SHA blob readback:

| Path | Git blob | Change and scope |
| --- | --- | --- |
| src/vres_os/install_recovery.py | ac780fab49d8ca94d343f91e3d4b774f8be3bf46 | M +17/-1; v2 moved plugin backup must hash-match original snapshot digest; refuse mismatch/unprovable; preserve v1 legacy-backup behavior |
| tests/test_backup_recovery.py | 90b590aa6276049346ae3bf4b71014ac732ebaa7 | M +38; new parametrized edited/extra/missing plugin backup negative cases and missing digest refusal with zero mutation |
| scripts/personal_upgrade_rehearsal.py | f0375e307c90c69608398a8368f1911692cb0ceb | A +256; stdlib-only Git-object candidate staging, P2 original hook identity check, synthetic previous plugin/launcher/Claude tree snapshot, interrupted upgrade and actual recovery code, exact rollback check, corrupt-backup refusal |

**Original installer, hooks, migrations, credentials, model/Chairman, live task/DB modules untouched.** Feature publication used exact A18 parent and nonforce CAS expected-old lease, and remote HEAD/tree and exact three-file compare/readback were verified.

### M1 disposable boundary

The rehearsal reads original P2 Git commit objects (not local installed files), validates P2 hook Git blob and SHA256 against Stage6, stages from the M1 pinned commit into NEW temporary directories, verifies Git-based release manifest and *copied* package/plugin. It sets up fake original P2 current-user-shaped installation and synthetic Claude/global files, fake unrelated plugin and auth marker, uses actual install_recovery.snapshot/inspect/recover functions on those temp files, simulates plugin/pointer/launcher/Claude updates, verifies complete original byte map restored and no extra credential/other-plugin mutations, then independently simulates corrupted P2 backup hooks and requires refusal with no mutation. Temp files are deleted. **It does not run pip, the actual install.ps1, Claude, hooks, Vres CLI, PostgreSQL, secrets or a real project.** It is a staged package-copy / simulated installation with real offline recovery-code exercise, not physical installed acceptance or independent process/network isolation.

## 4. Validation matrix — distinguish evidence types

| Gate | Status |
| --- | --- |
| GitHub main/docs/P2/A18 HEAD/tree/ancestry | **PASS (GitHub read)** |
| P2 vs A18 source release contract/001–041/exclusion review | **REVIEWED STATIC** |
| M1 HEAD/tree/sole parent/exact three-file allowlist and new blobs | **PASS (GitHub readback)** |
| M1 Python unit tests and source parsing on actual candidate | **NOT_RUN** |
| Git-object source staging/manifest/package/plugin verification on Windows | **NOT_RUN** |
| Disposable synthetic P2 → candidate interrupted upgrade and rollback | **NOT_RUN** |
| Corrupted backup refusal and no mutation | **NOT_RUN** |
| M1 Windows process env restore, pre/post protected blob/worktree checks | **NOT_RUN** |
| Actual installer, pip, installed P2, native Claude, PostgreSQL | **NOT_RUN / PROHIBITED** |
| A18 historical selected Windows test | **49 PASS at A18 SHA only, not M1** |
| Independent native Claude M1 review | **NOT_RUN / BLOCKED** |

### Exact next action — ONE complete operator Windows script

Archived docs path: docs/handoffs/VRES-M1-INTEGRATED-OFFLINE-WINDOWS-GUARDED-TEST-2026-10-30.ps1. This is one entire SHA-pinned native Windows PowerShell 5.1 block, also provided inline in the responding chat. Do not execute from Claude Code.

The guarded script uses the existing original P2 anchor **C:\Projects\Vres-P2F-Postinstall-Hardening-20261022**, verifies exact 82c8243 HEAD and clean protected worktree, fetches only official GitHub M1 feature branch (Git hooks disabled), creates *new* detached P1 checkout at **C:\Projects\Vres-ChatGPT-Review-Personal-M1-Upgrade-20261030** (refuses existing path, preserves all historical worktrees), verifies candidate HEAD/tree/parent and exactly A/M/M changed paths, checks 9 pinned protected blobs before and after, cleans and verifies changed process environment and restores caller directory. Performs a single stdlib offline rehearsal and selected test modules tests/test_release_artifact.py, tests/test_install_contract.py, and targeted tests/test_backup_recovery.py; requires both command exits0, checked JSON pass markers and clean post-test worktree. Final marker **VRES_PERSONAL_M1_WINDOWS_OFFLINE_EXECUTION_PASS_PENDING_EVIDENCE_EVALUATION** is only meaningful when observed in actual transcript.

If any FAIL/BLOCKED, preserve original console, exact SHA and worktree without patching installed P2, touching credentials or bypassing incidents. A source fix would require another exact-parent feature commit with failed evidence preserved, NOT false acceptance. No native Claude reviewer while host-hook incident open.

## 5. Development path to DAILY PERSONAL USE

**M1 now:** Await one meaningful Windows offline acceptance. If PASS, accept only as versioned PERSONAL source candidate with *simulated* rollback, **not installed**.
**M2:** Resolve host-hook and LIVE_SCHEMA_048 incidents separately, and obtain explicit P2 consent plus rollback before any installed version change. Do not reopen Stage7 matcher loops.
**M3:** #165 Chairman, session/task continuity, #176 relevant experience/procedures, practical low-friction daily flow.
**M4:** #166 global Claude/PRISM and #168 project adoption safely preserving user's existing state.
**M5:** #163/#164 credential broker and #167 approved same-Windows-user cross-project secret handles/data source registry; offline catalog first, no live DB until separate clearance.
**M6:** #169 Visual Studio and real legacy project accepted with operator consent.
**M7:** #170 limited PERSONAL pilot, real tasks, rollback, operational readiness. Full production-ready status requires its actual acceptance evidence.
**M8:** advanced optional capabilities after dependable baseline.

Closed source dependencies #163/#164/#174; open #165/#166/#167/#168/#169/#170/#176, as in prior canonical index. Preserve ALL V-01..V-42: Chairman/task/model (V-01..07), specialists/tools (08..18), memory/E7/E8 (19..23), onboarding/research (24..26), credentials/project sources (27..33), release/DB safety and optional trust (34..37), Visual Studio/readiness/supply (38..40), real outputs and low-ceremony UX (41..42). Do not silently mark any as installed, accepted or deleted.

## 6. Follow-up and checkpoint instructions

After Windows test, user provides FULL console transcript and named pytest cases, exits and final PASS/FAIL marker; evaluate independently without native Claude while host-hook incident is open. Then archive exact results on canonical docs branch and proceed to separate M2 gates, only if M1 is accepted. A denied/broken test is a negative record, not an invitation to run database/Claude. Hard automatic checkpoint at/before reply 20 or context conservatively >50%, whichever earlier: publish all authorized completed changes on correct branches by exact-parent nonforce lease, dated handoff and canonical index newest READ FIRST; supply FULL fresh-chat resume prompt in ONE inline fenced block and recommend next chat. No background promise.

**No new Windows test, actual install, credential/real project contact, PostgreSQL action or native Claude Code invocation was performed in this GitHub-only milestone.**
