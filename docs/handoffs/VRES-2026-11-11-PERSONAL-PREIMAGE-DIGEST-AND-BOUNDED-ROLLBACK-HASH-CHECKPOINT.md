# Vres-OS — 2026-11-11 original activation preimage digest + bounded rollback hash HARD continuity checkpoint

## READ FIRST — owner direction, single personal product and authorization

This is ONE integrated production-quality PERSONAL daily-operations Windows app for ONE current user. Keep the original Chairman, tasks/work sessions/completed-result history, original Credential Broker and data-source store, global/project Claude adoption, Experience Intelligence and the original release owners. NO enterprise IAM, multitenancy, duplicated task/memory/data/credential stores, second Chairman or disconnected apps. Preserve the ENTIRE original V-01..V-42 register; M0..M8; W0..W3; W4 R1..R13. Every formerly held original product ambition remains development scope, NOT runtime authority.

Owner direction: continue substantive source-only integrated development before ONE final nonsensitive owner-selected Windows Claude Code dummy-project UAT, rather than repeatedly running Windows tests after micro-milestones. Authorized now: safe GitHub source/test/docs commits on correct dedicated source and canonical documentation branches. NOT authorized: physical Windows/profile changes, real credentials/legacy project, installed P2 changes, host Claude/hooks, PostgreSQL even SELECT, protected merges, installers, releases or Windows UAT.

Repository https://github.com/vosser24/Vres-OS; stable GitHub ID 1368577038, connector admin/push permissions true at this checkpoint. Canonical docs branch: docs/chatgpt-continuity-20261023. First read the LIVE docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md and this document, previous 2026-11-11 bounded-source/current-target handoff and earlier dated rollback/KEEP/source/target/intent/freshness/activation/consent chain. Read docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md and original integrated roadmaps, and LIVE issues #165–170, #174, #176 and #185. Verify actual remote refs, trees/parents (where accessible), blobs, compares, CI and issue states afresh. GitHub is NOT proof of any Windows installation or local unpushed work.

## Incoming verified state, independent static review and discovered defects

Incoming docs branch HEAD 7680cf2f77898363bddeac0d350694fe588a225c; constructed TREE 642f2757d101cadddf6036423ba034fbad5ca98f; intended parent 2f01a95200932cba0e5dbf55a44f8f97689fb99a; index blob b663e14d65c10304f9477d5358a129749f8dc226; immediately previous handoff blob 61d8070f5ffc5fce4b0b3dd3a3b0adc99fbfde02. At this session's publication, update EXACTLY this index and the NEW handoff; resulting commit/blob/tree values must be verified and recorded, never predicted.

Incoming source branch feature/personal-legacy-current-target-observation-20261111 HEAD 7515cbdf7582e9f6b1d7444819bf887b1fcf18b2; created TREE 03ee36fb9603172db47b727f87c6138c56ebb575; intended sole parent b372969a0292faea38b3f58e4a8ec5f0b9e62d6b; project_adoption.py blob 498772f74d4c0861edf17c6b71b15810d4df50da. Previous bounded source commit b372969a0292faea38b3f58e4a8ec5f0b9e62d6b created TREE 14f405534f2b6f4441953ee520647294c0d4a4f4 and exact intended parent cda6ce3eaefa933ed5bb88929728518ac74545dc. Source and synthetic test diffs were statically inspected, including the shared bounded reader, inventory/snapshot/activation call sites, saved original KEEP source proof, current target plan, closed-loop re-attestation and existing #165 session assertions. No source code or import/test was executed.

P1 SUBSTANTIATED: b372 introduced an activation regression. In original #168 activate(), the prepared preimage persisted manifest entry referenced variable digest, which was no longer assigned after replacing unbounded Path.read_bytes() with _read_verified_preimage(..., expected_sha). For a present project surface, this would raise UnboundLocalError before completing the manifest. This is a code-path reasoning conclusion, NOT a live observed failure. No activation, project mutation or host run occurred.

P2 SUBSTANTIATED: original _sha_or_none() still used unrestricted Path.read_bytes() after lstat, although it is invoked by activation pre-DROP checks and before/through rollback/recovery. The operation could open re-bound leaf bytes or unbounded current content and lacked the shared post-read descriptor/ancestor rechecks. This is a cooperative race/size guard, not evidence of exploitation or atomic filesystem assurance.

No independent protected #185 external verdict was supplied or inferred. Current selected-target observations and original KEEP source checks still DO NOT prove a durable NEW-target preimage, safe reversible proposed action, actual owner permission or Fable validation.

## Source correction 1 — P1 verified digest manifest integrity

NEW dedicated branch: feature/personal-adoption-preimage-digest-integrity-20261111.
PUBLISHED and remotely read back HEAD **5da70a9f64eafbdcbf75aed20aef97d2d5da2531**.
Git tree created: **f6d9f2aaaa9bad1f28d80972e841b681a0bec320**.
SOLE intended parent: **7515cbdf7582e9f6b1d7444819bf887b1fcf18b2**.
Exactly TWO changed original-owner paths:
- src/vres_os/project_adoption.py blob **79869644c33ee9d4dd0cf3f0785af12ccb860013** (+1/-1). The manifest records expected_sha, already format-checked and compared to the bounded bytes before the copy; no new approval or write authority.
- tests/test_project_adoption.py blob **f7ae471a12e956611d3f91db543a24a512c8585d** (+26/-0). ONE synthetic disposable-legacy test authored NOT_RUN. It checks saved preimage exact SHA and raw bytes and restores them via the existing original rollback path when run safely in the future.

Created source/test blobs, exact base TREE, exact-parent Git commit, branch from pinned parent; non-force update_ref(expected_sha=7515cbdf...) succeeded. Remote branch blob SHA readback and compare 1 ahead/0 behind, EXACT two paths verified. Connector fetch_commit returned the commit and its diff. Raw independent Git commit parent/tree REST readback NOT available; do not confuse object-construction evidence with independent raw REST proof.
Commit: https://github.com/vosser24/Vres-OS/commit/5da70a9f64eafbdcbf75aed20aef97d2d5da2531

## Source correction 2 — P2 bounded original activation/rollback digest check

NEW dedicated branch: feature/personal-adoption-restore-bounded-hash-20261111.
PUBLISHED and remotely read back HEAD **446a330a9244c62ebc67c7bbd15a59a857e2cf4f**.
Git tree created: **c5acd3d0a86691abfefaa905113ce424c1e0e897**.
SOLE intended parent: **5da70a9f64eafbdcbf75aed20aef97d2d5da2531**.
Exactly TWO changed original-owner paths:
- src/vres_os/project_adoption.py blob **3ba803f68c7e1762667a42314814f4ae1f77e4cd** (+9/-1). Existing _sha_or_none preserves absent=None and link/special refusal, but uses _read_verified_preimage(path.parent, path.name, None, ...) for bounded ordinary current bytes before SHA. Applied to existing activation, rollback and recovery callers; no new store, credential, host, DB or authority. Cooperative NOT atomic and not a blanket Windows security certification.
- tests/test_project_adoption_bounded_source_races.py blob **ab689e815c9349c026cf116e174e5c187d5029ec** (+30/-0). TWO synthetic functions authored NOT_RUN: leaf rebind at open should refuse and an oversized current file should refuse before hashing.

Non-force ref update with expected_sha=5da70a... succeeded; remote source and test blob readback matched created blob objects, fetch_commit diff was inspected, compare vs parent 1 ahead/0 behind with exact TWO paths. Full latest source vs original 074adb10c58c30625c3eb705ca2926b9d8442997 is **10 ahead/0 behind**, exactly SIX original-owner source/test paths (project_adoption.py, personal_work_session.py, test_project_adoption.py, test_project_adoption_bounded_source_races.py, test_project_adoption_fresh_resume_integrity.py, test_personal_work_session.py).
Commit: https://github.com/vosser24/Vres-OS/commit/446a330a9244c62ebc67c7bbd15a59a857e2cf4f

## Test provenance, CI, rejected attempts and unverified states

Incoming source had **102 related synthetic test functions AUTHORED NOT_RUN**. Exactly ONE new test from commit 5da70a plus TWO new tests from commit 446a33 = **105 related functions AUTHORED NOT_RUN; ALL 105 NOT_RUN**. Existing test functions and work-session assertions from previous checkpoint remain included as previously counted. This is authored test code, NOT proof of a test pass. Python AST/compile NOT_RUN. Isolated exact full-source transfer NOT_PROVEN. COMPLETE transitive no-DB/no-host/no-native-Claude import and tests/conftest safety NOT_PROVEN. Focused pytest NOT_RUN; repository-wide pytest NOT_RUN; simulator NOT_RUN; Windows Claude dummy UAT NOT_RUN; installed P2 acceptance NOT_RUN. The test conftest was read statically; it has active initialization/audit-hook and child-process policies and cannot itself prove test execution safety. BOTH new source commits had empty GitHub combined-status arrays and empty observed associated PR-triggered workflow-run arrays. CI PASS UNVERIFIED; the PR workflow filter is limited, not an exhaustive Actions search. Historical Linux 35 focused PASS and Windows result-history 8/8 PASS at 04808884f27b9db722bc529e927962c36654488a, and work-finish 7/7 PASS at 258467ad0465f706c993444175efdaca026769fb, remain pinned historical results. NONE transfer to latest HEAD.

Preserve original failed/rejected attempts: 54237bf7, 10379454, 0df5ada1, 3cabcb99, 5ea64136, 5addd2a0; earlier regex/backslash/CLI/pytest, source replacement, isolated transfer/DNS and memory patch failures; earlier uncommitted rejected blobs cc60e529 and 6f85150f; current-target patch duplicate-anchor refusal, superseded uncommitted candidate blobs d1554498, 09219bd7, 483e54ee and corrected first handoff candidate c7fa8f33. These are historical, not merged as accepted tests. Documentation publication evidence: first non-force docs update_ref invocation returned an internal tool error after the proposed Git commit was created. An immediate live docs compare (0 ahead/0 behind) and old index blob readback proved the branch had NOT moved. One subsequent non-force update_ref with the unchanged exact expected_sha succeeded; remote index/handoff blobs, commit and two-path compare were independently verified. No force, assumed success or concurrent overwrite occurred. Two direct public raw-Git-commit REST web opens returned inaccessible; raw parent/tree REST independence remains UNVERIFIED, not claimed. No issue, incident, authorization or hold was cleared.

## Protected baseline / product versus GitHub evidence

Protected product main current HEAD **9a8acc5d464b96432a93cb95daa9581412fb07ee**, inherited TREE **659d3fdd6e635dbaecbd5c492ba7279754edaec7**, original parents 6af7bddf246e0f628c3e52add9528742e85189ca and 8ae041721bf0418f6472ab541b6838fd73fec46a: LIVE compare exact SHA against main IDENTICAL (0/0). No main merge or source write.

Protected R13 branch feature/personal-w4-r13-universal-staging-hold-20261106 at HEAD **bcf62460d68caebfdbd0e838d44c5997992c5fbc**, inherited TREE **9bbc5615fef4a8f785e9ddb0056e9430ffe25d63**, intended parent 0badcd34d1eafbce5f815512a489d70cb240eecd: LIVE compare identical 0/0. No write or release.

Historical P2 source pin 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. Actual physical Windows installed state, protected local Windows worktrees, unpushed PC files, user profile, credentials and Claude behavior UNKNOWN. GitHub changes are SOURCE ONLY, not physical Windows acceptance.

ABSOLUTE HOLDS — ALL OPEN:
- LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL EVEN SELECT, direct/indirect.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code/hooks.
- Original P3 incident OPEN; independent trusted F1/Fable high positive authority NOT_GRANTED.
- W4 R13 universal staging/release HOLD ACTIVE; #185 independent three-verdict external security review NOT_RUN.
- NO host/Windows/profile change, installed P2 overwrite, real credential, real legacy project/wizzard_9, real TASK-DAY-01, protected local worktree, installer/migration/release, main merge or automatic UAT.

## EXACT NEXT authorized operation / original integrated roadmap

1. LIVE read canonical docs index/new handoff and previous bounded-source/current-target checkpoint; reverify repository, latest docs/source/main/R13, constructed trees/sole intended parents, changed blobs, ancestry and CI. Treat no raw REST commit parent/tree as unverified independently, not as fabricated proof.
2. Independently STATIC REVIEW 5da70a and 446a33 for correctness and compatibility of expected_sha, _sha_or_none, link/size/rebind fail-closed behavior, all activation/rollback/recovery callers and the THREE new synthetic tests; scrutinize the previous b372969a and 7515cbdf source and six authored tests too. Correct only substantiated further defects on a new exact-parent dedicated feature branch.
3. Tests may be executed ONLY if exact isolated pinned full-source transfer and COMPLETE transitive no-DB/no-host/no-Claude dependency/conftest safety are independently proved. Otherwise preserve **105 AUTHORED NOT_RUN**; never call native Claude/hooks, DB or ordinary CLI to make progress.
4. Build meaningful ORIGINAL #168/#174 target-specific durable NEW-target preimage/reversible rollback DESIGN AND SOURCE CONTRACT, exact source/current target binding, interrupted captures and restoration handling, separate attributable owner consent, independent protected F1/Fable validation and explicit manual gates before any new proposed project write. Current read-only status/plan observations cannot become owner approval, durable captured preimages, Fable authority or write permissions by declaration.
5. Continue integrated ORIGINAL #165 Chairman UX/governed family & effort policy/model routing/history/proposals; original task/work-session/completed-result saved replay; #163/#164 Credential Broker/secret-safe ingress; #166 current-user global Claude/PRISM adoption/rollback; #167 existing Data Source Registry/current-user catalog/freshness/project binding with no PostgreSQL contact; #176 original Experience Intelligence memory/provenance/freshness/contradiction/revocation/retrieval; #169/#170 verification/recovery/release design and original #174 architecture governance, all within V-01..V-42 and M0..M8/W0..W3/W4 R1..R13. Prioritize practical integrated PERSONAL milestones over standalone stores or endless test-only increments.
6. Publish every authorized completed source/test/doc change on the correct dedicated branch with exact parent, non-force expected-SHA lease and remote readback. Never merge main or touch R13.
7. ONLY at substantive completion, after separately proved incident clearance, independently trusted positive F1/Fable and NEW explicit owner host permission: ONE final nonsensitive owner-selected Windows Claude Code dummy-project UAT. NOT NOW.

## HARD continuity checkpoint protocol

At or before the 20th completed assistant reply following THIS VERIFIED docs checkpoint, or sooner if context reliability/consumption becomes uncertain, stop feature phases, reverify live GitHub/hold state, publish a NEW dated detailed docs/handoffs/ checkpoint and prepend canonical index using exact parent and expected-SHA non-force, verify remote blobs/compare. Preserve tests PASS/FAIL/NOT_RUN with true provenance, SHAs, parents/trees, all rejected history, protected worktrees, original requirements, unresolved incidents, owner decisions and exact next operation. Supply ONE fully actionable fresh-chat resume prompt in a single inline fenced code block containing verified docs SHA/TREE plus URLs. End this chat and start a new chat. Never claim background execution.
