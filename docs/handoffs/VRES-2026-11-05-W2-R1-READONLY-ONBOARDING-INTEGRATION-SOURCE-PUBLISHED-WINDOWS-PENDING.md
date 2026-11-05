# Vres-OS — 2026-11-05 W2 R1 read-only onboarding integration: GitHub source PUBLISHED, Windows pending

**Scope:** PERSONAL Vres-OS daily operations for ONE Windows user. This is a bounded W2 source-development increment. NOT a claim that full W2 real onboarding, native Claude, installed release or protected Fable approval is complete.

**READ FIRST:** docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, this dated W2 handoff, the prior dated W1 R2 accepted offline Windows handoff, and the complete 2026-11-05 V-01..V-42 roadmap. All previous original requirements, history, rejected attempts, accepted P1 real task and P2 safety restrictions remain intact.

## 1. Live GitHub continuity verification and exact ancestry

- Repository: https://github.com/vosser24/Vres-OS
- Canonical docs branch: docs/chatgpt-continuity-20261023
- Verified PRE-W2-docs docs HEAD: 09a53e29b908c8c32490ec341a62550f135986a8
- Verified PRE-W2-docs docs TREE: 3fdde0be9c73efa6b6ea347069d5acf119abf2f0
- Verified PRE-W2-docs docs sole parent: 6508a626c3c660057fe3337f579357d1af4595dd
- Product main: 9a8acc5d464b96432a93cb95daa9581412fb07ee, TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7, NOT MERGED.
- Accepted W1 R2: branch feature/personal-w1-scratch-chairman-handoff-20261105, HEAD ba6568bb0028ed64e7f1ef41a5aa6ac9d3ac25bd, TREE e53780b07271bb1099c96fd651ee4b21ca22616b, sole parent 3aa3a7b33fb3c1cc2a5cd8a04d0ed9b0f8739fbf.
- W2 R1 new branch: feature/personal-w2-onboarding-integration-20261105.
- W2 R1 PUBLISHED remote feature HEAD: fa45e2aed729e11675c0a3effe56156901d82acf.
- W2 R1 TREE: 58b36cc905cbcb2aa257266704276a39142723f3.
- W2 R1 SOLE parent: exact accepted W1 R2 ba6568bb0028ed64e7f1ef41a5aa6ac9d3ac25bd.
- W2 feature commit: https://github.com/vosser24/Vres-OS/commit/fa45e2aed729e11675c0a3effe56156901d82acf
- Exactly TWO ADDED paths, no modification to original W1, project_adoption, global owner, protected DB, hooks, installer, SQL or core CLI:
  * src/vres_os/personal_w2_onboarding.py, Git blob 7ac3a5e1f4227d488a0027ba790d202b0c96dd53; local SHA256 1bbfd0c8cdc7da8fd0541db91e33537a51d0038aaf9b481e658a23c28c17fe8f.
  * tests/test_personal_w2_onboarding.py, Git blob a4734fb4902517f7e5bb35adc97f4a25414b40b1; local SHA256 5773881a5398f186c8b27084ce0534e97eb47d28817d7902cfcf1a02c42b66af.
- Both remote GitHub blobs matched exact local Git blob SHA-1 before commit creation. Remote commit TREE, sole parent and recursive tree blob entries verified before ref update. Feature was published with nonforce expected-old-SHA lease, and remote branch readback matched HEAD. Main, W1 and old docs remote refs still matched expected values immediately after feature publication.
- Current source line compared to main: W1 R2 105 commits ahead, zero behind. Accepted relevant historical feature/issue branch issue-174-engineering-architecture-governance and feature/168-personal-legacy-claude-architecture-activation-fence-20261030 are ancestors of W1 R2; no blind merge was performed.

## 2. Actual source contracts independently inspected in current GitHub

#166 current-user global Claude adoption is NOT enterprise global authority. It owns synthetic inventory and classification, immutable-fixture modeling, no native/vendor-state reading, sealed per-number KEEP/DROP review, failure/interruption and exact rollback demonstration. Relevant source owners already present in W1 are global_claude_adoption_plan.py, global_claude_fixture_transaction.py, global_claude_migration_review.py, global_claude_synthetic_operator.py and global_claude_disposable_disk_fixture.py.

#168 project adoption owns project_adoption.py (includes start, decide, activate, recover, rollback and status), project_preview.py (stateless read-only), and personal_project_intake.py (read-only user-facing renderer). IMPORTANT: project_adoption.start CAN create scaffold and durable state, and was NEVER invoked here on a real project. #168 current inventory categorizes executable config as DROP-only and refuses stale decisions. Established legacy activation requires #174 architecture alignment plus separately protected Fable/high positive review; KEEP/DROP alone is insufficient.

#174 owns architecture_governance.py and deterministic plan checking; this is NOT independent Fable approval and does not clear the held protected validator. W2 R1 explicitly composes these original owners rather than creating a new scanner, project store, Chairman, launcher or task DB.

## 3. What W2 R1 actually adds

The added read-only source module composes #168/#174 preview with an optional ALREADY-CREATED #166 built-in synthetic global migration demo session. Output is bounded canonical JSON with hashed canonical project-key/root binding, project inventory and architecture gates, synthetic demo decisions and journal/rollback summary, explicit current-user scope, full un-cleared safety holds and explicit false flags for activation, real consent, independent Fable and project/profile writes.

The module:
1. Makes an integrated first-use packet for fresh versus legacy/established project classification; it NEVER calls project_adoption.start or accesses installed/user data itself.
2. Refuses a forged, modified, cross-project or stale scan packet, and a synthetic demo revision mismatch before recording further demo choices. Its freshness contract explicitly covers scan-time Claude inventory/structural architecture findings ONLY, not the bytes of every source file or a signed authority.
3. Forwards numbered synthetic KEEP/DROP only to existing #166 immutable session logic; unresolved choices cannot freeze a plan. Frozen demo remains INACTIVE PREVIEW, not permission to apply KEEP or DROP to user data.
4. Reuses the exact accepted #166 disposable fixture logic and #168 actual adoption operations THROUGH ONE TEST ONLY, with pytest tmp_path synthetic roots and synthetic test authority.
5. Refuses to imply native Claude launch, current-user global-home inspection, credential access, PostgreSQL contact or P2 installation.

The single test tests a fresh minimal project read-only preview then synthetic #168 scaffold (only CLAUDE.md; no fake skills/agents); stale preview refusal; established legacy source plus executable settings and retained bytes; #174 architecture hold and no activation; invalid KEEP of executable settings; stale inventory refusal; bounded KEEP/DROP; #166 synthetic interruption + sealed review + exact rollback; synthetic choice freezing; and separately a small benign legacy project exact activate/rollback via existing #168 owner. The active environment, actual current-user project, real HOME, installed state, hooks and DB are never targeted.

**Gap:** This is W2 R1 READ-ONLY INTEGRATION SOURCE ONLY, not full #166 current-user disk adoption, actual legacy migration, real global quarantine, durable production cross-profile journal or final W2 native UAT. No first-launch activation authority granted.

## 4. Test evidence and provenance

- AUTHOR LOCAL Python 3.13.5 syntax/compileall of both new files: PASS (local isolated container, NOT native Windows).
- AUTHOR LOCAL narrow preflight of coordinator against deliberately stand-in owner APIs: 1 PASS in 0.08 seconds. This mock-only test was NOT committed, not a substitute for real dependencies.
- GitHub source/test blob-byte hashes, prepared exact-parent Git tree/commit, nonforce expected-SHA branch write and remote ref+commit readback: PASS (direct GitHub connector observation).
- ONE COMMITTED end-to-end full-original-source pytest integration test: AUTHORED, NOT_RUN, not PASS, as original repository/source dependencies were unavailable to the current container. A local static Python compilation is not a pytest acceptance.
- Independent second-agent source/security review: NOT_RUN. Ordinary Claude Code tools are forbidden while HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED is OPEN; do not silently substitute a claimed independent reviewer.
- Exact original-source disposable Windows W2 integration: NOT_RUN. No approved Windows W2 gate or original-source host test conducted.
- Native Claude UAT, actual user profile/global adoption, real legacy project changes, P2 install and real PostgreSQL: HELD/NOT_AUTHORIZED.
- GitHub CI was NOT invoked manually. The inspected existing workflow executes PostgreSQL tests on main push or PR. This new branch update is not a main push or PR; no workflow-based database testing is authorized or claimed.
- No observed host-local effects; source and Python tests here were run only on sandbox container test paths. No external host egress attestation.

## 5. Important limitations and security notes

- Even a matching W2 scan digest is NOT an exact file-byte snapshot for all project source files. Existing #168 activation must rescan and independently validate on actual consent/hold clearance.
- The current-user Claude HOME is explicitly NOT inspected; the built-in #166 demo is NOT a real migration proposal and synthetic caller text is not verified user approval.
- The single synthetic small legacy activation/rollback in authored tests is restricted to pytest tmp_path when later run. It is not an authorization to invoke project_adoption.activate or start against real projects, current-user HOME or installed profiles.
- No independent trusted F1/Fable authority. No physical-host observation. Full W2 acceptance remains PARTIAL/NOT_RUN.
- No ordinary vres CLI, native Claude Code, installed hooks, installer, update.ps1, install.ps1, PRISM, credential store or PostgreSQL access. No product main merge or installed P2 overwrite.
- Protected installed P2 historically derives from source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; current Windows installed identity was NOT independently refreshed.
- Original real personal TASK-DAY-01 remains COMPLETED, zero active and one completed snapshot by previous owner-pasted evidence. Do not reopen, create test tasks in the real desk, or touch the original Markdown or three retained P1 portable apps.
- Original W1 R1 rejected attempt, Python py-launcher unavailable, Python quote TypeError, Powershell FINALLY/policy and historical R2 acceptance, P1 and #168 tests/branches remain documented in preceding continuity entries, not silently cleared or rerun.
- Preserve all original V-01..V-42, M0–M8, #163/#164/#165–170/#174/#176, E7/F2/C2B/R0, Stages 1–6 and owner approval boundaries.

## 6. Absolute holds (still OPEN)

- LIVE_SCHEMA_048_INCIDENT=OPEN. NO PostgreSQL even SELECT; no direct or indirect DB invocation.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN. NO ordinary native Claude, hooks, real Claude UAT or incidental installed plugin route.
- Independent trusted F1/Fable positive authority NOT GRANTED.
- Protected P2 installation NOT_AUTHORIZED.
- No PRISM, real secret/data-source handle, legacy source edit, current-user profile change, installation, update, main merge, Windows Sandbox R2 launch or PowerShell execution-policy change.
- No implicit approval from "proceed" to perform P2/real-host modifications.

## 7. One exact next operation, W2 acceptance before W3

1. Reverify latest canonical docs branch HEAD/TREE/parent and index, feature W2 R1 HEAD fa45e2aed729e11675c0a3effe56156901d82acf TREE 58b36cc905cbcb2aa257266704276a39142723f3 sole parent ba6568bb0028ed64e7f1ef41a5aa6ac9d3ac25bd and both added exact Git blobs. Verify main/W1 refs still current.
2. Independently review both W2 files in their exact entirety against original #166/#168/#174 owners. In particular examine test fixture realism, stale decisions, project root alias/symlink handling, F1 hold, no native executable import and exact protected-state effects. Do not claim independent review if none can safely run.
3. Prepare ONE pin-verified FULL ORIGINAL-SOURCE disposable offline integration gate for W2, running focused test_personal_w2_onboarding.py, not accepted W1 historical suites and not DB/Claude/hook import paths. Verify actual signed Python and offline dependencies; no unsigned shims, pgAdmin/PG Python, user-profile state or installed P2. The Windows operator must separately authorize NEW disposable-only roots and run the exact inspected gate before a Windows PASS can be accepted.
4. Analyze any real failing integration assertion against actual GitHub byte-pinned source, fix ONLY impacted paths on a new exact-parent commit, publish nonforce lease, targeted rerun. No artificial PASS/whole-suite treadmill.
5. After verified W2 integration, evaluate remaining W2 real global-home/onboarding capability as HELD until host incident/positive Fable consent. Continue W3 synthetic provenance/reuse next, W4 integrated reproducible package next, then independent G1 and specific P2 install permission, #169 Visual Studio UAT, #170 personal pilot.
6. Keep author, independent reviewer, physical Windows, GitHub source and NOT_RUN provenance separate. Do not issue a real Claude execution/update script while holds stay open.

## 8. Publication bookkeeping

This dated handoff and its READ FIRST index insertion are documentation-only additions on canonical docs branch. They do NOT alter the product feature branch or any real Windows application. Verify their published commit SHA/TREE/sole parent, exact new handoff blob, updated index blob and remote branch readback. Do not claim success if GitHub refuses any write. Use the resulting current GitHub docs HEAD as the new fresh-chat checkpoint. 
