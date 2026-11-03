# Vres-OS — 2026-11-03 HARD CONTINUITY CHECKPOINT: integrated M2 + #167 offline Windows ACCEPTED, 254 PASS / 3 SKIP, next activation holds

**Status: VERIFIED SOURCE-LEVEL PERSONAL INTEGRATED OFFLINE ACCEPTANCE, NOT LIVE INSTALLATION.**
**Date:** 2026-11-03 Europe/Athens.
**Product identity:** practical PERSONAL daily-operations application for ONE Windows user, NOT enterprise IAM/multi-tenant/SaaS.
**Repository:** https://github.com/vosser24/Vres-OS
**Canonical documentation branch:** docs/chatgpt-continuity-20261023.
**Canonical READ FIRST:** docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, which should contain THIS handoff as its newest entry after the exact-parent documentation commit.
**Prior canonical docs HEAD before this checkpoint:** **b2d860d0136befff57914dd7b8a5f127e53f10d0**, tree **8c6392068a8cfaec30d854d1532e21f4d92636cc**, sole parent **1c60e7fa15aa53be4cb03e5bc52579b00b3c4b72**. The NEW docs SHA/tree cannot be known before this handoff's eventual GitHub commit; reverify actual remote ref, tree and newest READ FIRST at fresh-chat start. No main merge or product-source edit is part of this checkpoint.

## 1. Most recent operator evidence — ORIGINAL POSTFLIGHT FILE

The user submitted the full native Windows PowerShell 5.1 Start-Transcript file **VRES-M2-167-Postflight-20261103-130201.txt**, mounted at /mnt/data/VRES-M2-167-Postflight-20261103-130201.txt during the current chat. Exact original raw bytes were inspected by Python/container:
- **9,298 bytes**, **177 text lines** (178 if counting the final empty line in a newline-based rendering); mixed CRLF and LF text line endings, UTF-8 BOM.
- **SHA256:** **1f97ed4794d3e64241b292b33a4a9c7d34fd2d7acbd5718c04d73bda18affa45**.
- Original raw Git blob SHA1 **ee8dbd58adc271d37c6ba140705d6db5b21cbca8**, computed locally but **NOT PUBLISHED** because the original includes a machine name, account name and environment metadata.
- Transcript records normal Windows PowerShell 5.1, one atomic **READ-ONLY** postflight script from docs/handoffs/VRES-2026-11-03-M2-167-INTEGRATED-POSTFLIGHT-READ-ONLY.ps1 Git blob **9cdfdaf053decd76321d51cee960137f184ca90f**.
- All **30 actual key output markers** (not private host/user header) were preserved in **docs/handoffs/VRES-2026-11-03-M2-167-INTEGRATED-READ-ONLY-POSTFLIGHT-PASS-SANITIZED.txt**, Git blob **650c512bb1c6c5638254b55e9c665120ed03b844**. This is a SANITIZED EXCERPT of original markers, not byte-identical raw original; keep uploaded original with user.

**Original postflight OBSERVED PASS markers:**
- SHA256 identity of **integrated-pytest-full.txt** and **release-inputs.txt** stored in the original Windows TEMP fixture: PASS.
- Exactly **254 unique named PASSED** pytest cases plus **3 documented SKIPPED Windows symlink-privilege cases**: PASS; no repeated or substituted count.
- Protected original P2 Git anchor exact HEAD: PASS; original protected anchor reported clean and official Git origin checked by the executed script, with no output anomaly.
- POST integrated source HEAD **7a1d2da36f9ef1475e7909ca8850b9b641380b1d**: PASS.
- POST integrated Git tree **98658c0270b65032f38ab38c0671c48b2a291bc1**: PASS.
- POST single accepted M2 parent **a65215a3b8b91ad4ab374c928ae3cf667e5b0f95**: PASS.
- POST exact seven-source-file changed-path allowlist relative to M2-HOST baseline: PASS.
- **17 protected source/test Git blobs** all PASS: install.ps1; src/vres_os/install_recovery.py; tests/test_install_rollback_proof.py; src/vres_os/personal_data_sources.py; src/vres_os/personal_data_source_store.py; tests/test_personal_data_sources.py; tests/test_personal_data_source_store.py; tests/test_install_contract.py; tests/test_install_preflight.py; tests/test_backup_recovery.py; tests/test_release_artifact.py; src/vres_os/release_inputs.py; src/vres_os/release_artifact.py; src/vres_os/database_targets.py; src/vres_os/credential_broker.py; plugins/vres-os/hooks/hooks.json; tests/conftest.py.
- POST integrated detached review worktree CLEAN: PASS.
- **POSTFLIGHT_PASSED_CASES=254**, **POSTFLIGHT_SKIPPED_CASES=3** and final **VRES_M2_167_INTEGRATED_READ_ONLY_POSTFLIGHT_COMPLETE_PENDING_EVALUATION** are present.
- NO Python/pytest rerun, native Claude, PostgreSQL, real Vres installer, Credential Locker value or real user-profile mutation from this postflight.

**Verdict:** the previously incomplete postflight has now genuinely COMPLETED. Accept the exact integrated candidate's **selected SOURCE-ONLY Windows offline suite** and source integrity gate at its fixed SHA/tree with **254 PASS, 3 SKIP, exit0**, and static release inputs 001–041 exit0. Do NOT call it actual installed rollback, native host/Claude safety, a database contact audit, F1/Fable positive validation, Windows owner ACL validation, full #167 issue closure or production readiness.

## 2. Related selected Windows run — exact chain of evidence; retain two rejected wrappers

**Underlying Windows combined pytest upload:**
- User provided original full PowerShell Start-Transcript VRES-M2-167-Integrated-R1-20261103-123403.txt (57,450 raw bytes, SHA256 **b4aa6bfd7c61e15bff00fa538e71f0a90a853aa523c50ea259949f8958653cf6**, raw Git blob 4e30c0f507a5eb900a83b971c79edeb1d31b358b, **PRIVATE, not committed** because of machine/account identifiers).
- Original P2 source anchor, official GitHub remote, integrated source HEAD/tree/sole parent and exact seven-path allowlist, **17 PRE Git blobs PASS**.
- Windows source static release input validation: **"personal-release inputs valid: migrations 001-041 pinned, no experimental files"**, explicit **RELEASE_INPUTS_EXIT_CODE=0**. No database migration/contact.
- Selected native Python 3.12 pytest: **254 DISTINCT NAMED PASSED, 3 SKIPPED, zero reported FAILED, PYTEST_EXIT_CODE=0**.
- Test module breakdown: 19 test_install_rollback_proof.py, 20 test_install_contract.py, 43 test_install_preflight.py, 79 test_release_artifact.py, 44 test_personal_data_sources.py, 33 test_personal_data_source_store.py, 16 selected test_backup_recovery.py. Total 254.
- The three **SKIPPED** store tests are Windows symlink-privilege cases, two reported at tests/test_personal_data_source_store.py:217 and one at :234. Symlink/reparse coverage in those cases **NOT_RUN** on user's Windows environment. Do not enable Developer Mode / elevate privilege without separate consent. Other hard-link and synthetic negative tests did pass; real Windows current-user owner-only ACL / icacls behavior in production **NOT_RUN**, tests use synthetic ACL callbacks.
- LIVE APP-DATA FENCE unexpected refusals=0, integration_opt_in=False, process environment restoration PASS.
- Operator's captured TEST FILES (not separately uploaded as raw files, but matched exact SHA256 in completed read-only postflight): integrated-pytest-full.txt size **71,168 bytes**, SHA256 **CA068AE86CF62E63E7041710AD8962EE330C2D97B0518F74D521A1FA0D286FFB**; release-inputs.txt size **164 bytes**, SHA256 **CAE4096DFF7D155555E9AF4CF1DD9F8639624575ED02508C55953A2A2D17B010**.
- Individual PASSED and skipped case identities preserved publicly ONLY in an explicitly sanitized/authored roster, **docs/handoffs/VRES-2026-11-03-M2-167-INTEGRATED-254-PASS-3-SKIP-CASE-ROSTER.txt**, blob **4e8ccff7941a343661e8833214542c76c24bce27**.

**Preserve BOTH original integrated operator wrapper failures as history:**
1. Original attempted integrated PS script Git blob **53e51b031d0db0433aff0fc17c8f66094b178728** had malformed "$label:" interpolation: **PowerShell parser rejection, NO commands executed**, NOT_RUN.
2. Corrected R1 script Git blob **11ca2355235bde1b8f1f3512c5e7ec0a616991e1** compiled and ran all intended preflight, release-input and pytest tests, but erroneously demanded an aggregated regex "[0-9]+ passed" even though pytest output contained 254 individual PASSED lines and no aggregate. Its **OUTPUT-CHECK wrapper refused after pytest exit0**, leaving final Git postflight NOT_RUN in that particular block. That is NOT a pytest failure. The new complete **READ-ONLY postflight** verified saved logs and all 17 Git blobs, closing this exact evidence gap without rerunning tests. The original rejected scripts remain immutable and their errors documented; do not reclassify rejected attempts as green.

**No duplicate count:** the original user's troubleshooting diagnostic repeated some last test rows and skips; the 254 roster counts each actual native summary ID once. The completed read-only postflight separately checked the saved log contains exactly 254 unique test PASS lines and the two skip group rows summing to 3.

## 3. Exact committed GitHub product/source boundaries

**PERSONAL integrated accepted OFFLINE source feature:**
- Branch: **feature/personal-m2-167-offline-integrated-release-20261103**
- Remote HEAD: **7a1d2da36f9ef1475e7909ca8850b9b641380b1d**
- Tree: **98658c0270b65032f38ab38c0671c48b2a291bc1**
- Sole parent: accepted M2 rollback branch commit **a65215a3b8b91ad4ab374c928ae3cf667e5b0f95**, tree **942a4a4d29bdae64314de6490e4e8f99674dbf3e**, parent accepted M2-HOST **526fb9d61e4a61c26c19931f9adf2d68eecd1bc8**, tree **9919f363a8608e31e4c5a6f66adb765c7021b484**.
- Commit: https://github.com/vosser24/Vres-OS/commit/7a1d2da36f9ef1475e7909ca8850b9b641380b1d
- Relative to M2-HOST base 526fb9d6, EXACT seven-path union: M install.ps1 (Git blob 8b5dd6dcc3cc8315f7a4c27d0173b4963b52d933), M src/vres_os/install_recovery.py (b35d559758e3b6721f43631dc499095f7895c5f3), A tests/test_install_rollback_proof.py (f6fb2ab35dc6e39302437d7e1931f9e92220a55d), A src/vres_os/personal_data_sources.py (ad08616bf89d34c0c5f52affff30813562d7a2f7), A src/vres_os/personal_data_source_store.py (debd4368428ca14273ad64a6c2d4f3c583ad92d2), A tests/test_personal_data_sources.py (46c66bc83bac97e67ed7538f9413d871d04b2ee2), A tests/test_personal_data_source_store.py (c3d901ca42f5f5ae66687e6ed194d3d14f60ac2f).
- This candidate is a versioned source/tree union, NOT merged to main, NOT an installed artifact, NOT independently trusted F1 validation; it includes previously selected offline changes only. No PostgreSQL, real credentials, native hooks, real legacy project, or installed profile have been altered by this acceptance.

**Source milestones historically accepted / evidence-bounded:**
- #168 A18 feature/168-personal-record-leaf-rebind-a18-20261030, **7bace7758e5c7f9a00f26179eb741ef3a319bc77**, tree **4d17344a9510de6394840092cf33729ab153fbb5**; 49 selected Windows PASS historically.
- M1 integrated source **28120eb49b6b950c7402455db19dcbdcf6d991a6**, tree **815fce697f16509bae150729891738d879d6ca9c**, parent A18; 110 named selected Windows PASS, synthetic rollback and tampered backup refusal, original initial preflight excerpt omission preserved.
- M2-HOST source **526fb9d61e4a61c26c19931f9adf2d68eecd1bc8**, tree **9919f363a8608e31e4c5a6f66adb765c7021b484**, parent M1; 63 selected Windows PASS/exit0, process env and protected blobs PASS with excerpt limitations.
- Separate M2 rollback proof **a65215a3b8b91ad4ab374c928ae3cf667e5b0f95** tree above; bounded selected Windows pytest exit0 but original Start-Transcript lacked case roster. Integrated combined suite now supplies 19 dedicated M2 rollback PASS and 16 selected backup recovery PASS under the combined fixed source.
- #167 original source **16f8df95a001527bdd1ed94dfd3a963016109384**, tree **54cc836906b1f63e074e0aebf2e24cb5e7b875fd**, first Windows **REJECTED 43 PASS/1 FAIL exit1** due static source-path typo. Original 114-line uploaded CRLF output SHA256 52c544e875862a4a0db173a9e31e25ea38bd145e2e24a56eb9cbbcc49149b8e2, immutable Git blob 425b56761430de26ac0620aaaa9a730ebfa49717. Keep rejected branch/worktree.
- #167 R1 corrected one test-path only **f909f61ab95a25fdfae5fbe3412ba233165f15b7**, tree **ee0a5cabae177f8febd42fa06d6c450c7cfe7f3d**; Windows 44 unique selected PASS/exit0, initial preflight excerpt omitted.
- #167 owner-scoped persistent store **2cb4f975e235a89fac5186e3529dbd492d8b6972**, tree **697f6ce12eb3c9c23338e20180a6ffd204bac40e**, parent R1; isolated Linux 80 PASS; initial separate Windows selected exit0 without case listing, now confirmed under integrated Windows suite as 33 selected PASS and 3 Windows symlink SKIP, with 44 pure-catalog PASS.
- Product **main** verified remote HEAD **9a8acc5d464b96432a93cb95daa9581412fb07ee**, tree **659d3fdd6e635dbaecbd5c492ba7279754edaec7**; never merged in this session.
- Original installed current-user Windows **P2 release last locally observed source** **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, tree **205c081277ece483c634e1c801c39595abd4549c**, installed hooks blob **5833973d9be6ccf4263dda2d461cc5994d30416c** (SHA256 700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7). This installed release identity is HISTORICAL, not freshly observed from user's machine in this turn. Passing protected original P2 Git ANCHOR is NOT proof current installed release has changed/unchanged today.
- Original personal release migration limit still **001–041 pinned only**; no experimental schema-048/C2B/R0/F2/migrations 042+ allowed in actual personal release. The source-only 001–041 check PASS does not physically contact a database.

## 4. Binding incidents and P0/P1/P2/P3 approvals

**LIVE_SCHEMA_048_INCIDENT=OPEN — NO PostgreSQL even SELECT**, direct or indirect. NO CLI, MCP, doctor, bootstrap, native hooks, migration, F2, recovery, schema inquiry or alternate target SQL even as a "read-only test". Running isolated synthetic offline pytest is not clearance. Do not contact original live schema under any pretext, do not execute SQL.

**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN — NO ordinary native Claude Code or installed hooks/plugin validate.** Seven historic posttool Read/Grep automatic hook attempts routed into a held database and were refused. Source Stage3–6 matcher narrowing (9 to 0 from original installed P2) and current GitHub source are NOT an independently trusted full native-host no-route acceptance. No installed hook hotpatch, no Stage7 matcher microtest treadmill. Do not tell user to launch Claude in another directory as a workaround. Original Stage6 release provenance and protected worktrees remain authoritative.

**Independently trusted F1/Fable-positive high authority NOT GRANTED**; preserve denied protected validator/model actions. Chairman Opus/medium exists as candidate-only offline policy module; installed preview Sonnet/high and any actual runtime model unchanged/unverified. Do not silently raise effort, activate Fable, bypass denied F1.

**P0:** read-only GitHub source/document analysis and design, safety case, documentation.
**P1:** one bounded feature branch, safe offline synthetic tests and protected worktree, explicit consent by user's execution when necessary; preserve evidence and errors.
**P2:** explicit, specific user approval BEFORE changes to installed P2, current Windows profile, actual Credential Locker/secret handles, global Claude/PRISM, real legacy project or model, after relevant P3 holds closed and exact rollback plan/changed-path list prepared.
**P3:** absolute open incident holds above; no exception implicit in "continue development". No product main PR/merge or go-live without separate explicit approval.

This project remains **PERSONAL single-Windows-user daily operations**, not enterprise IAM. Minimize ceremony/microtests, prioritize coherent useful milestones. Never claim user-profile/credential/installed artifacts accessible from GitHub. ChatGPT cannot see local unpushed Windows changes except user-provided logs, and cannot work asynchronously.

## 5. Protected rejected evidence, worktrees, failures and issues

Preserve original rejected A12 **345a568b551ac23183c54f10611335adee903b96** 18PASS/1FAIL exit1, original rejected A13 **cdaa39aaa774cef88a4831bf6b157e380fbb69d9** 28PASS/1FAIL exit1, corrected R1s distinct. Preserve A16 original environment restoration *copied script* proof ambiguity, A19 blocked/uncommitted, original #167 43 PASS/1 FAIL, integrated PowerShell syntax-rejected script + separate false "summary string" wrapper refusal, PT1/PT2A/PT2B/PT2C/PT2D, Hook-R1, A1–A18, Stage1–6, E7/E8/C2B/R0/F2, original live schema-048 incident, F1/Fable trust denial. No failed result may be upgraded retroactively because a later separate attempt passed.

**Protected local Windows worktrees (paths historical, not re-read now):**
- Original P2 anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 (HEAD 82c82430..., read-only by operator).
- Original rejected #167 C:\Projects\Vres-ChatGPT-Review-167-Offline-Catalog-20261103 — DO NOT remove/reset.
- #167 R1 C:\Projects\Vres-ChatGPT-Review-167-Offline-Catalog-R1-20261103.
- M2 rollback proof C:\Projects\Vres-ChatGPT-Review-M2-Rollback-Proof-20261030.
- #167 owner-scoped store C:\Projects\Vres-Review-167-Personal-Store-20261103.
- **Accepted integrated source evidence worktree:** C:\Projects\Vres-Review-M2-167-Integrated-20261103; POST Git clean and 17 blobs PASS, no deletion/reset. Windows TEMP logs for this run remain evidence.
- Additional historical PT/Hook/R0 protected original Windows worktrees remain in the older canonical docs; none is disposable by default.

**Issue status verified live from GitHub this checkpoint:**
- #163 Credential Broker CLOSED (source history only).
- #164 secret-safe onboarding CLOSED (source history only).
- #174 architecture/Fable-validated adoption planning foundation CLOSED (source history only, NOT independent F1 positive on protected operations).
- #165 Chairman model policy configurable Opus/medium + host-observed monitoring OPEN.
- #166 global current-user Claude adoption / KEEP-DROP rollback OPEN.
- #167 current-user data-source registry and read-only semantic catalog OPEN despite offline source progress.
- #168 project adoption and canonical Claude scaffold OPEN.
- #169 integrated Windows Visual Studio/PRISM + real legacy project live acceptance OPEN.
- #170 personal production readiness OPEN.
- #176 experience intelligence governed learning, episodic memory and retrieval OPEN.

**Scope:** preserve full original V-01 through V-42 EXACT titles, statuses, explanations and acceptance paths. Original register: docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md, blob c6c8c24e4a38efb2e7589017e98b43b2015821df. Full 42-row M0–M8 product/dev/Windows board docs/roadmap/VRES-PERSONAL-LOCAL-WINDOWS-ACCEPTANCE-AND-FULL-DEVELOPMENT-BOARD-2026-10-31.md. Charter docs/architecture/VRES-PERSONAL-SINGLE-USER-PRODUCT-CHARTER-AND-METHOD-2026-10-30.md, blob f50d3a0adf4bf2c885c3aa719bd9d3e66e21fcb6. No requirement dropped, no enterprise scope injection.

## 6. EXACT next development action in the NEW ChatGPT session — DO NOT REPEAT PYTEST

This is a **HARD OWNER-DIRECTED CONTINUITY CHECKPOINT**. All authorized work this turn was acceptance assessment, a sanitized GitHub evidence/handoff/board/index documentation commit ONLY; no product-source/test changes needed. When this docs checkpoint is published and verified, **END THIS CHAT** and start a NEW ChatGPT Project chat.

The FIRST OPERATION in new chat:
1. Verify latest canonical GitHub **docs/chatgpt-continuity-20261023** HEAD/tree/parent and newest READ FIRST which must be THIS handoff. Verify main 9a8acc5d..., accepted offline integrated source 7a1d2da3..., M2 and #167 branch identities; read complete report and original 42-item scope board. Never start with a stale history entry.
2. Treat exact integrated M2+#167 source **7a1d2da36f9ef1475e7909ca8850b9b641380b1d**, tree **98658c0270b65032f38ab38c0671c48b2a291bc1** as **ACCEPTED for selected Windows OFFLINE source and release-input validation only**: 254 distinct PASS, 3 Windows symlink SKIP, pytest exit0, 001–041 release input exit0, original P2 anchor and Git 17 PRE+17 POST blobs, env restoration and clean worktree PASS. Stop demanding repeated 254-suite runs for a previously completed result. Preserve symlink/physical ACL limitations as NOT_RUN.
3. **Next useful milestone:** prepare ONE proportional, practical **M2 LOCAL ACTIVATION READINESS & INCIDENT DISPOSITION** work package in safe GitHub-only P0/P1 scope: reconcile source release manifest/actual P2 pinned provenance, the native Claude host-hook DB-route incident and LIVE_SCHEMA_048 prohibition; identify independent no-contact host-boundary evidence and exact bounded operator P2 consent/rollback procedure without calling normal Claude, PostgreSQL, real credentials, real installed hooks, real legacy projects or user-profile writes. If independent trusted no-contact proof cannot be obtained, leave incidents OPEN and explicitly report the blocker rather than inventing clearance or running an unsafe command. Avoid Stage7 matcher microtests or endless reviews; treat these as ONE integrated go-live safety gate. Do not start actual install.ps1.
4. Only when each incident is separately cleared by evidence and user authorization, present specific personal release deployment proposal: exact file allowlist/release source SHA/tree, backup and byte-preserving rollback, current-user profile impact, model/Claude/PRISM scope, explicit user P2 approval, live onboarding after safe hooks; do NOT merge product main automatically.
5. Continue practical M3 Chairman, task/session/experience, M4 current-user Claude/PRISM/fresh/legacy adoption, M5 same-user Credential Broker and data source catalog user-facing linking (NO live PostgreSQL until separately cleared), M6 Visual Studio #169, M7 actual personally authorized pilot #170, optional M8, with full V-01..V-42. User can benefit from offline features while holds remain; do not block ALL GitHub source work.
6. Report current source-only feature #167 issue still OPEN; real Windows symlink privilege tests **3 SKIPPED**, owner-only ACL adapter not yet physically tested, real Credential Broker values/DB actual catalog not tested; document those as future authorized acceptance, not hidden defects.

**Hard 20-reply / context >50% auto-checkpoint rule continues**. At or before 20 assistant completed replies or conservatively approaching half context (precise meter unavailable), stop new feature phases; verify GitHub HEAD/tree/parent plus available installed source provenance; commit all authorized completed source/tests/docs on exact-parent non-force expected-SHA branches and remote readback; update newest READ FIRST and detailed dated docs/handoff; give a FULL fresh-chat resume prompt INLINE in exactly ONE complete fenced code block as well as handoff/commit GitHub links and exact verified docs SHA/tree, explicitly recommend NEW CHAT, STOP current session. No background work or invented tests/incident clearance.

## 7. Publication provenance and immediate constraints

The new documentation commit that contains this handoff must:
- Have exact old parent docs HEAD **b2d860d0136befff57914dd7b8a5f127e53f10d0**, tree **8c6392068a8cfaec30d854d1532e21f4d92636cc**;
- Modify only canonical docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md and update the existing full board's newest acceptance addendum; ADD only this full dated handoff and a sanitized operator postflight marker evidence excerpt; no source/test/hook/main edits;
- Be published with expected-old-SHA nonforce lease; re-fetch remote and verify HEAD/tree/sole parent, exact four changed docs paths, current main/integrated branches unchanged and all 42 original roadmap requirement rows intact.
- In the terminal answer give user a complete next-chat resume prompt with the ACTUAL NEW docs HEAD/tree and exact next milestone, no missing steps and no stale NOT_RUN postflight claim.

**Current evidence bottom line:** the original integrated Windows source offline 254-pass/3-skip run + new 17-blob READ-ONLY postflight are both observed and complete. The M2+#167 integrated candidate is accepted at the selected offline source/release-input level. The two P3 incidents and actual installed daily-operations readiness remain OPEN/NOT_RUN. Treat these as distinct facts, not contradictory status.
