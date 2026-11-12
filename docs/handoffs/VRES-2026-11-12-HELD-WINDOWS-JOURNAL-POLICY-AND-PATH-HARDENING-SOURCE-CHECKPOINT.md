# Vres-OS — 2026-11-12 source-only Windows held-journal policy and path hardening checkpoint

## READ FIRST — product, owner direction and absolute boundaries

Continue ONE integrated production-quality PERSONAL Windows daily-operations application for ONE user. Build ALL original V-01..V-42, M0..M8, W0..W3, W4 R1..R13 and preserve C2B/K0 historical protections; no enterprise IAM, multitenancy, second Chairman, duplicate task/credential/memory/data stores or disconnected standalone applications. OWNER DIRECTION: meaningful product source development before ONE final nonsensitive owner-selected Windows Claude Code dummy-project UAT; no Windows live UAT after every small milestone.

Safe GitHub SOURCE, synthetic-test AUTHORING and documentation on correct dedicated branches only are authorized. No installed Windows/P2 changes, Windows profile/protected worktrees, real credentials, real legacy project, PostgreSQL even SELECT (directly or indirectly), native Claude/hook execution, actual TASK-DAY-01, installer, migration, release, R13 activation, automatic rollback/project remediation or main merge. Never infer physical Windows state from GitHub.

Original owner boundaries: #165 ONE Chairman, configurable generation-tolerant Opus/medium policy, governed routing and HOST-OBSERVED telemetry, conversational UX, proposals, tasks, work sessions, completed-result history and replay; #163/#164 original Credential Broker/secret-safe ingress; #166 current-user global Claude/PRISM adoption, quarantine, numbered KEEP/DROP, recovery and rollback; #167 original current-user Data Source Registry with Broker links, structural/semantic catalog, provenance/freshness and explicit project bindings WITHOUT DATABASE CONTACT; #168 ORIGINAL project_adoption.py is the sole fresh/legacy/active/interrupted/scaffold/target capture/recovery owner; #174 original architecture governance (historically closed issue, NOT independently granted protected Fable/high); #176 original Experience Intelligence/provenance/revocation/reuse; #169/#170 verification/recovery/release; #185 genuinely external 3-verdict security review NOT_RUN.

## INCOMING LIVE GITHUB PIN — VERIFIED IN THIS CHAT

Repository https://github.com/vosser24/Vres-OS ID 1368577038, default main.
Incoming canonical docs HEAD af1be1330f4569504e26d0bc25842c535f463b77 TREE d49e0581686b69156fa82ee88b04b9c22147c5a7 PARENT ea21aa18935f2788bab24d810d9e71a0fd86c486; INDEX BLOB e522f16a7d83dffdc42cef1c84389bf79af0455b; preceding handoff blob 3ff412aa3fa46865047cb8b86e845cdb911cf503.
Incoming source branch feature/personal-held-windows-root-acl-handle-probe-20261112 HEAD e9c80477ff0fcf139c6af71f9c5ade6bfaa71a06 TREE a99278c0a76204c591eddf012460e83531be1a4b SOLE PARENT 0afb7775aa6d8c2ca3b8027b8fa44e280af69c23; 25 ahead/0 behind original source 074adb10c58c30625c3eb705ca2926b9d8442997, EIGHT unique source-test paths.
Protected main HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7, protected R13 branch feature/personal-w4-r13-universal-staging-hold-20261106 HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63, unchanged on incoming verification.
Historical installed P2 SOURCE PIN 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. Physical Windows installation, actual user-profile/protected worktree, local unpushed changes, credentials and native Claude state UNKNOWN.

Read the canonical index first, prior held Windows private-root ACL/handle source handoff, prior DPAPI source handoff, private storage/recovery design, prior 2026-11-12 same-state/inverse/recovery/Chairman handoffs, 2026-11-11 activation/consent/recovery history, original docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md, integrated roadmaps from October 22/30/31 and November 5, 2026, and live #165/#166/#167/#168/#169/#170/#174/#176/#185. Current issue status verified: #174 CLOSED historically (NOT authority); all listed others OPEN.

## INDEPENDENT STATIC REVIEW — FINDINGS AND LIMITATIONS

Reviewed exact incoming Windows _windows_held_storage_probe.py blob 99d1e7811accee658d14930599d01808c1c7332a, current _windows_held_privacy.py blob 438c9bad95a3e4fb724476aa5b6c3a35424ce60b, original #168 wrappers and incoming tests as static source. Checked SHGetKnownFolderPath FOLDERID_LocalAppData GUID and CoTaskMemFree, process SID/thread impersonation refusal, ctypes/WinDLL argument and handle shapes, no-follow CreateFileW, GetFileInformationByHandle and NTFS identities, GetSecurityInfo/LocalFree, DACL protection/Allow ACE checks, component path restrictions, project/state overlap, redacted diagnostics and unproven races.

Substantiated P2 defense-in-depth defect in syntactic path policy: Microsoft Windows reserves device aliases COM¹/COM²/COM³ and LPT¹/LPT²/LPT³ (also with extension), but incoming _local_drive_components had only ASCII numbered aliases. Windows docs: https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file. New source refuses those superscript names before any Win32 call.

Other reviewed limitations REMAIN OPEN: component-by-component CreateFileW handles are NOT atomic handle-relative confinement or race proof; protected DACL/owner checks are only read-only observations and no DACL is created; unknown alias/8.3/substitution windows and owner/SYSTEM policy need independent review; token check and SID/ACL can race; DPAPI ciphertext is not authenticated Fable evidence; no distinct-principal negative ACL test, no actual Windows DPAPI/ACL run, no encrypted persistent journal, no crash durability, no real Windows consent. Do not claim the review independently attests Windows ABI correctness or WPR gate completion.

## PUBLISHED SOURCE COMMIT — NON-FORCE EXACT PARENT / REMOTE READBACK VERIFIED

NEW branch: feature/personal-held-windows-journal-policy-and-path-hardening-20261112
HEAD: 51c090ff4affeb9223c7b6c909b35455f07f8c83
TREE: 115542ae243fdd71988052cff1e9530c74ff0513
SOLE PARENT: e9c80477ff0fcf139c6af71f9c5ade6bfaa71a06
COMMIT: https://github.com/vosser24/Vres-OS/commit/51c090ff4affeb9223c7b6c909b35455f07f8c83

Exactly FOUR changed source/test paths, verified remote:
1. ADD src/vres_os/_windows_held_journal_policy.py, blob cb05533b88133b9023ca5a4195de00578d69f06e, 176 lines. Pure bounded metadata with exact fields, capture/project/plan/selected-number identity, finite PREPARING -> COPIES_SEALED_HELD / RECOVERY_REQUIRED and COPIES_SEALED_HELD -> RECOVERY_REQUIRED proposals, strict monotonic revision, exact predecessor STRUCTURAL SHA256, no authority fields, no filesystem/Windows code, fail-closed restart triage. Each result EXPLICITLY denies verified readback, writes, automatic recovery and Fable.
2. MODIFY src/vres_os/_windows_held_storage_probe.py, blob 933d17d80ffff62703f37273e68b8eebf67f3f62, +3 lines: refuse Windows reserved COM/LPT superscript device names.
3. MODIFY src/vres_os/project_adoption.py, blob bc5d4bf73727ea5da920e5f348df80aab8a8038f, +22 lines: lazy PURE candidate wrapper inside the ORIGINAL #168 owner; never invoked by active capture, recovery, project write or Chairman approval.
4. MODIFY tests/test_project_adoption_fresh_resume_integrity.py, blob e64b9e63d6782dbc2165ba6e171f9c8f42fe00e7, +129 lines: FIVE new synthetic tests AUTHORED NOT_RUN.

Source new HEAD compared to sole parent: 1 ahead/0 behind, FOUR files; full ancestry vs original 074adb10c58c30625c3eb705ca2926b9d8442997 = 26 ahead/0 behind, NINE distinct source/test paths. Ref moved from exact parent by non-force expected-SHA lease; remote ref, commit/tree/sole parent, changed paths and all FOUR exact file blob SHAs read back and verified. No product-main merge, Windows host action or protected R13 mutation.

Important source limits: the canonical SHA256 previous-record hash is NOT a MAC/signature; a forged record can recompute it. The planner does not create/read a durable journal, decrypt DPAPI, authenticate manifest/seal, verify exact preimages or assert positive authority. A missing journal may hide orphan copies; any sealed-looking claim must be independently reverified. ORIGINAL _held_capture_private_storage_available() still returns FALSE on Windows and MUST REMAIN FALSE without trusted external proof + authorization.

## TEST / CI PROVENANCE

Incoming 163 related synthetic test functions AUTHORED, all NOT_RUN. Five NEW functions AUTHORED, all NOT_RUN:
- test_held_windows_root_path_refuses_superscript_device_aliases
- test_held_windows_journal_policy_genesis_and_seal_are_non_authorizing
- test_held_windows_journal_policy_refuses_lineage_downgrade_and_identity_drift
- test_held_windows_journal_policy_refuses_forged_authority_or_secret_metadata
- test_held_windows_journal_restart_triage_never_automates_recovery

NEW TOTAL 168 related synthetic functions AUTHORED; ALL 168 NOT_RUN. Exact isolated pinned COMPLETE-source transfer/full transitive no-DB/no-host/no-native-Claude import/conftest safety NOT PROVEN. Whole-source AST/compile NOT_RUN. Focused pytest NOT_RUN, repo-wide pytest NOT_RUN, Windows DPAPI/ACL/handle test NOT_RUN, Windows dummy UAT NOT_RUN. Latest pinned source combined statuses [] and associated workflow runs [] — neither equals PASS; latest CI PASS NOT VERIFIED. Any older pinned PASS is historical only for that exact earlier revision. The source-only static review is NOT runtime/test/independent security certification.

## PRESERVED ABSOLUTE HOLDS / REJECTED HISTORY

LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT, direct or indirect.
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code or hooks.
Original P3 incident OPEN; independently trusted F1/Fable/high positive authority NOT_GRANTED; #185 genuinely external independent three-verdict review NOT_RUN; WPR-01..WPR-10 NOT_PROVEN/OPEN/NOT_GRANTED; R13 staging/release HOLD ACTIVE.
NO protected local Windows worktree, user profile, installed P2, real credentials, real legacy project, real TASK-DAY-01, installer, migration, release, automatic UAT, project remediation, rollback, product-main merge. All Windows physical identities UNKNOWN.

Preserve rejected commits 54237bf7 / 10379454 / 0df5ada1 / 3cabcb99 / 5ea64136 / 5addd2a0; rejected blobs cc60e529 / 6f85150f; superseded commits d1554498 / 09219bd7 / 483e54ee / c7fa8f33; prior unpublished DPAPI staging blobs 7c73027f24503a531e02b1b24a63cd60cd22e174 / 382dd3e325470a5c0473c9a3213f01f607a4458b. Preserve original host-hook/DB and P3 incidents, activation/recovery chronology, source/DNS transfer errors, CLI/conftest/pytest failures, protected worktrees and PASS/FAIL/NOT_RUN exact source pins. Never claim an incident or UAT cleared.

## EXACT NEXT OPERATION FOR NEW CHAT

1. Read LIVE canonical index and THIS newest handoff plus preceding Windows ACL/DPAPI/recovery/Chairman handoffs, architecture design, original functionality register/roadmaps and issues. Independently verify repository ID, docs HEAD/tree/parent/index/handoff blobs, newest source HEAD/tree/sole parent/all four blobs, compare/ancestry, protected main/R13 refs/trees and CI status. Never infer Windows state.
2. Independently STATIC REVIEW exact new 51c090ff source with particular attention to pure metadata type/size bounds, revision and predecessor shape, sequence refusal, forged hash/authority assertions, and integration being lazy and non-authorizing. Correct substantiated defects on a NEW dedicated exact-parent source branch, not on main/R13.
3. Continue SUBSTANTIVE original #168/#174 owner-private Windows secure-storage SOURCE implementation: owner-only protected DACL creation + descriptor/readback candidate; trusted process/current-user token, child handles/no-follow path confinement, Windows volume/file IDs, reparse/junction/hardlink refusal; DPAPI context-bound encrypted payload/manifest/seal; exclusive PREPARING / COPIES_SEALED_HELD / RECOVERY_REQUIRED durable journal with file flush, atomic replace, crash/restart recovery and no plaintext spill; exact source/target/postimage/inverse readback; independent WPR-01..10/F1/Fable evidence; separately attributable CAPTURE and HUMAN project-WRITE consent. NONE is authorized to execute on the real host now. Do not simply flip capture gate TRUE.
4. Continue original ONE #165 Chairman routing/telemetry/conversation/proposals/tasks/sessions/result replay, #166 current-user global Claude, #167 Credential-Broker-linked Data Source Registry WITHOUT DATABASE CONTACT, #176 Experience Intelligence, #169/#170 recovery/production and full original V-01..V-42. Integrated useful milestones before ONE final nonsensitive owner-selected Windows Claude dummy UAT, only after independent incident/Fable clearance and NEW explicit host approval.
5. Run synthetic tests ONLY after independently confirming exact isolated pinned COMPLETE-source transfer and full transitive no-DB/no-host/no-native-Claude import/conftest safety. Otherwise all 168 remain NOT_RUN. Preserve complete source/test evidence and rejected histories.
6. Publish any authorized source/test/docs changes on NEW dedicated exact-parent source and canonical docs branches using blob/tree/commit, NON-force expected-SHA leases and remote readback. Do not merge main or touch R13/Windows/DB/native Claude/credentials. Keep original owners and product personal.
7. Hard auto-checkpoint at/before 20 completed assistant replies since last verified checkpoint or earlier if context reliability requires: dated detailed GitHub docs/handoffs entry and continuity index newest READ FIRST; verify docs SHA/tree/parent/blobs; supply FULL fresh-chat resume prompt INLINE and links; END current chat. Never claim background work or precise context consumption without evidence.

NEXT MILESTONE: independently review 51c090ff then implement source-only private DACL creation/handle-relative confinement and actual encrypted durable journal I/O/restart recovery, without lifting any holds.
