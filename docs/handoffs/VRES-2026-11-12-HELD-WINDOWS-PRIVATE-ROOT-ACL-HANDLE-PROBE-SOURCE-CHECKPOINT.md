# Vres-OS — 2026-11-12 held Windows private-root ACL/handle PROBE source checkpoint

## READ FIRST — OWNER DIRECTION AND INVARIANTS

One production-quality PERSONAL daily-operations Windows app for ONE user. Continue ALL meaningful original integrated V-01..V-42, M0..M8, W0..W3, W4 R1..R13 and historical C2B/K0 protections. Build substantive PERSONAL functionality before ONE final nonsensitive OWNER-SELECTED Windows Claude Code dummy-project UAT, only after independent incident/Fable gates and fresh host consent. Do not repeat Windows UAT after each minor source phase.

Safe source/test AUTHORING and docs publication are authorized on dedicated exact-parent GitHub branches. NO PostgreSQL even SELECT, direct or indirect. NO ordinary native Claude Code/hooks. NO Windows host/profile, real credential, actual legacy project, installed P2, protected local worktree, actual TASK-DAY-01, installer, migration, release, product main merge, automatic rollback or project remediation.

Keep EXACT original owner boundaries:
- #165 ONE Chairman: configurable generation-tolerant Opus/medium initial policy, governed worker routing, HOST-OBSERVED telemetry, original conversation UX, proposals, tasks, work sessions, completed-result history and saved replay. It can surface the ORIGINAL #168 read-only reviewed state but cannot issue Fable authority or write projects.
- #163/#164 original Credential Broker and secret-safe ingress; no extra credential store.
- #166 global means CURRENT user's Claude/PRISM adoption, quarantine, numbered KEEP/DROP, recovery and rollback.
- #167 CURRENT-user Data Source Registry linked to Credential Broker, structural/semantic catalog, provenance/freshness and explicit project bindings; NO DATABASE CONTACT while incident open.
- #168 ORIGINAL project_adoption.py remains the only project adoption/held capture/recovery owner; fresh, legacy, interrupted, active, canonical scaffold, exact KEEP/DROP, reversible recovery.
- #174 engineering architecture governance; issue historically closed as foundation, not positive independent F1/Fable/high authority.
- #176 original Experience Intelligence and governed memory/provenance/freshness/revocation/reuse.
- #169/#170 verification/recovery/production readiness; #185 genuinely external independent three-verdict security review not run.
No enterprise IAM, multitenancy, second Chairman, duplicate state owners or disconnected mini applications.

## INCOMING CURRENT GITHUB — LIVE VERIFIED

Repository https://github.com/vosser24/Vres-OS stable ID 1368577038; default main.
Incoming canonical docs branch docs/chatgpt-continuity-20261023 HEAD ea21aa18935f2788bab24d810d9e71a0fd86c486 TREE 4e8a5cd99d9f768c87da7273a9b8838ba5e4c71b SOLE PARENT 99b08737bca6811fc3f0aa317227607123a62b88; index blob 84efeb4a045a97c34910f9b250f8f66999f7cd66; previous detailed DPAPI handoff blob 0bce0ccfb9187a6bbcfe3bbbf3a30ae16dfe2244. GitHub https://github.com/vosser24/Vres-OS/commit/ea21aa18935f2788bab24d810d9e71a0fd86c486.

Incoming source branch feature/personal-held-windows-dpapi-preimage-envelope-20261112 HEAD 0afb7775aa6d8c2ca3b8027b8fa44e280af69c23 TREE b5010f4896ca37e496678f2c97a1c678762c29b1 SOLE PARENT d36d3072b9e80cc748c3a6f39d52ba4b6bdd1209. GitHub https://github.com/vosser24/Vres-OS/commit/0afb7775aa6d8c2ca3b8027b8fa44e280af69c23.

Protected product main unchanged HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7. Protected R13 feature/personal-w4-r13-universal-staging-hold-20261106 unchanged HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63. Historical installed-P2 SOURCE PIN 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. Physical Windows installation identity, local protected/unpushed files, credentials and native Claude runtime UNKNOWN. GitHub cannot prove them.

Read LIVE canonical continuity index, previous 2026-11-12 held Windows DPAPI handoff, preceding same-state source checkpoint, 2026-11-12 personal Windows held-capture privacy/recovery architecture design, original V-01..V-42 functionality register, prior 2026-11-11 incident/activation/consent/recovery chronology, and live issues #165/#166/#167/#168/#169/#170/#174/#176/#185. Open issues except #174 historically closed. Preserve original October 22, October 30, October 31 and November 5 integrated roadmaps, all preceding 2026-11-12 recovery/inverse/preimage/root/Chairman/postimage/effect/target identity handoffs and 2026-11-11 history through canonical index.

## INDEPENDENT STATIC REVIEW OF INCOMING TOKEN-SID/DPAPI CODEC

Reviewed exact blob e3014afd64282d1ba51741a6d60893c54cc0c024 from incoming _windows_held_privacy.py, original #168 DPAPI wrapper, guard, and four incoming authored-not-run tests. Checked ctypes API signatures and memory lifetime for OpenProcessToken/GetTokenInformation/ConvertSidToStringSidW/LocalFree, DATA_BLOB and CryptProtectData/CryptUnprotectData, bounds/context serialization/entropy/sha256, redacted errors and path/secret-content handling.

The DPAPI envelope is in-memory, context-bound to a hashed project key, capture ID, selected number, exact plan digest and expected preimage digest, and does not persist files or enable capture. Output LocalFree and token closing paths are present in source; actual correctness on Windows is NOT_PROVEN. CryptProtectData does not turn SHA digest/DPAPI into independent Fable authentication, and same-user malware/privileged compromise remain out of scope.

One substantiated contract hardening gap: the source derives identity from the PROCESS token but did not refuse an impersonated THREAD, where the effective user/DPAPI context may differ. The new source refuses any available thread impersonation token via OpenThreadToken; ERROR_NO_TOKEN is the only allowed missing-token result. This is a source-only defense and not proof that thread/process identity cannot race or that DPAPI works on Windows. Microsoft Windows API references consulted:
- https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
- https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openthreadtoken
- https://learn.microsoft.com/en-us/windows/win32/secauthz/impersonation-tokens
- https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
- https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo
- https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle
- https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-getsecuritydescriptorcontrol

No Windows API execution or independent security review occurred here.

## NEW PUBLISHED SOURCE — EXACT PARENT, 4 PATHS, VERIFIED REMOTE

Branch feature/personal-held-windows-root-acl-handle-probe-20261112
HEAD e9c80477ff0fcf139c6af71f9c5ade6bfaa71a06
TREE a99278c0a76204c591eddf012460e83531be1a4b
SOLE PARENT 0afb7775aa6d8c2ca3b8027b8fa44e280af69c23
https://github.com/vosser24/Vres-OS/commit/e9c80477ff0fcf139c6af71f9c5ade6bfaa71a06

Exactly FOUR changed paths:
1. ADD src/vres_os/_windows_held_storage_probe.py, blob 99d1e7811accee658d14930599d01808c1c7332a, 370 added lines.
2. MODIFY src/vres_os/_windows_held_privacy.py, blob 438c9bad95a3e4fb724476aa5b6c3a35424ce60b, +18 lines.
3. MODIFY src/vres_os/project_adoption.py, blob bbb47f1a69c82a83c43994237010adb7c0a6a03a, +16 lines.
4. MODIFY tests/test_project_adoption_fresh_resume_integrity.py, blob 2012333b3223ec8bf34dae6f5b832d09e048b679, +51 lines.

Original #168 lazy internal diagnostic accepts exact project key/selected project root/state root and calls only when explicitly requested; it is NOT invoked from active capture/inspector/recovery. The Windows capture-storage gate still returns FALSE on Windows. This new module reads no file payloads, writes no paths and cannot authorize a project write.

Provisional source-only Windows candidate:
- Source PATH restriction rejects UNC/device/extended paths, alternate-data-stream characters, traversals, noncanonical separators, selected device aliases, trailing dot/space and oversized components before OS use.
- LOCALAPPDATA comes from SHGetKnownFolderPath instead of an arbitrary process environment variable; state root must exactly match original VresOS/projects/first-24-hex SHA256(project key) under this OS folder. Caller root overrides are not implicitly trusted.
- CreateFileW opens existing drive/ancestor/directory handles with OPEN_REPARSE_POINT/BACKUP_SEMANTICS; GetFileInformationByHandle observes NTFS volume/file index, directories, reparse and link counts, and refuses unsupported drive/filesystem.
- GetSecurityInfo reads current root owner/DACL from a handle, requires protected DACL, current process-token user owner, narrow user/SYSTEM allow-only ACEs, no inherited ACE, bounded ACE structure and sufficient effective user access.
- A second COOPERATIVE handle/DACL readback must equal the first, and selected project/state ancestor file identities must not overlap. The result is a redacted PROVISIONAL diagnostic with every capture/write/Fable/atomicity proof field FALSE.

IMPORTANT: component-by-component path opens are NOT handle-relative atomic confinement; static normalization is NOT OS normalization or a substitute for Windows adversarial testing. Does not create the owner-private DACL, lacks negative distinct-principal access proof, no actual DPAPI/file durability/manifest/seal/repair machinery, no independently trusted Fable or human project-write grant. A positive diagnostic DOES NOT ACTIVATE capture. Residual concerns include Windows ctypes ABI correctness, unusual reparse/alias names, races/A→B→A, privileges, ACL semantics and actual filesystem support. All require independent review/proof. WPR-01..WPR-10 remain NOT_PROVEN, OPEN or NOT_GRANTED.

Publication used 4 blobs and a tree based on the exact original e9c804 parent tree, a NEW dedicated branch created at the exact parent, NON-force expected-SHA ref lease, and remote ref/commit/tree/sole parent, exact file blob and parent compare readback. Entire source ancestry against 074adb10c58c30625c3eb705ca2926b9d8442997 is 25 ahead / 0 behind; exactly EIGHT unique source/test paths. No product-main merge. Main/R13 checked unchanged.

## TEST PROVENANCE — DO NOT CLAIM PASS

Incoming 160 related synthetic functions AUTHORED NOT_RUN. NEW three functions AUTHORED NOT_RUN:
- test_held_windows_private_root_candidate_rejects_unsafe_path_shapes
- test_held_windows_private_root_candidate_never_grants_write_authority
- test_held_windows_private_root_candidate_exact_path_shape_and_bounds

TOTAL 163 related functions AUTHORED NOT_RUN; ALL 163 NOT_RUN. These do NOT test actual Windows ACLs, DPAPI, races or crash/restart. No independent full transitive test-import/conftest no-DB/no-host/no-native-Claude safety proof; exact complete-source isolated transfer not proven. Complete-source AST/compile NOT_RUN. Focused pytest NOT_RUN. Repository-wide pytest NOT_RUN. Latest source Windows DPAPI/ACL test NOT_RUN. Final Windows Claude dummy UAT NOT_RUN. Latest source CI PASS NOT VERIFIED: combined statuses [] and associated commit workflow runs [] observed, NOT PASS. Older pinned Linux/Windows successful runs belong only to their own earlier source, NOT this commit. Preserve all original failed/rejected attempts.

## ABSOLUTE HOLDS AND PRESERVED HISTORY

LIVE_SCHEMA_048_INCIDENT=OPEN — NO PostgreSQL EVEN SELECT, direct or indirect.
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN — NO ordinary native Claude Code/hooks.
Original P3 incident OPEN.
Protected independently trusted F1/Fable/high positive verdict NOT_GRANTED.
#185 external independent three-verdict security review NOT_RUN.
R13 staging/release hold ACTIVE; WPR-01..WPR-10 OPEN/NOT_PROVEN/NOT_GRANTED.
NO Windows/user-profile changes, installed P2 overwrite, real credentials, actual legacy project, protected Windows worktree modifications, actual TASK-DAY-01, installer/release, product-main merge, automatic Windows UAT, real remediation or automatic rollback.

Preserve rejected attempts 54237bf7, 10379454, 0df5ada1, 3cabcb99, 5ea64136, 5addd2a0; rejected blobs cc60e529 / 6f85150f; superseded d1554498, 09219bd7, 483e54ee, c7fa8f33; DPAPI source staging superseded 7c73027f24503a531e02b1b24a63cd60cd22e174 and 382dd3e325470a5c0473c9a3213f01f607a4458b. Preserve historical DNS/transfer, source replacement, CLI/pytest/conftest/docs errors, prior CI identities, incident chronology, protected worktrees and source-specific PASS/FAIL/NOT_RUN evidence. No fabricated incident closure.

## EXACT NEXT OPERATION — NEW CHAT

1. READ live canonical index and THIS handoff, then independently reverify repository ID, docs/source/main/R13 refs, Git trees/parents/blobs/ancestry/diffs/latest CI/branch visibility, original roadmap and issue status. Do NOT infer physical Windows state.
2. Independently STATIC REVIEW exact e9c80477 source: SHGetKnownFolderPath GUID/CoTaskMemFree, token/impersonation checks, Windows ctypes calling conventions, CreateFileW handle flags and CloseHandle, GetFileInformationByHandle/FileInfo alignment, NTFS identity handling, GetSecurityInfo descriptor ownership/LocalFree, DACL/ACE bounds/mask/control, current-user SID, reparse/hardlink/8.3/DOS aliases, path component races, project/state identity overlap and three new NOT_RUN tests. Correct any substantiated defects ONLY on NEW dedicated exact-parent source branches.
3. Continue substantive ORIGINAL #168/#174 owner-private Windows state SOURCE ONLY, with trusted token identity, proven ACL creation/readback, handle-relative root and child confinement, DPAPI authenticated contextual envelopes, no plaintext persistence, PREPARING -> COPIES_SEALED_HELD / RECOVERY_REQUIRED exclusive durable crash-safe journal, correct manifests/seals and exact readback, interrupted crash/restart manual recovery, postimage/inverse verification, and separate human project-WRITE consent + truly independent protected F1/Fable/high. DO NOT activate real capture/project writes until independently verified WPR-01..10 and fresh permission.
4. Preserve and continue ORIGINAL #165 Chairman Opus/medium policy, governed routing/telemetry/proposals, task and work-session lifecycle, completed-result history/saved replay; #166 current-user global Claude adoption; #167 Credential Broker-linked Data Source Registry (NO DB contact); #176 Experience Intelligence, #169/#170 verification/recovery/release, complete V-01..V-42.
5. Synthetic execution only after independently verified exact isolated pinned COMPLETE-source transfer and full transitive no-DB/no-host/no-native-Claude import/conftest safety. Otherwise retain 163 NOT_RUN. No early Windows UAT.
6. For GitHub writes: exact parents, dedicated source/docs branches, NON-force expected-SHA leases, remote readback of commit/tree/parent/blobs/changed paths. Never touch main/R13, Windows, PostgreSQL, credentials, native Claude, installed P2.
7. Final ONE nonsensitive owner-selected Windows Claude dummy-project UAT ONLY after substantive integrated development, independently verified incident/Fable clearance and NEW explicit host consent. NOT NOW.

Hard continuity checkpoint at/before 20 assistant replies since last verified checkpoint, or earlier for context risk: create dated detailed handoff and prepend newest READ FIRST index entry; commit with non-force lease, read back exact docs SHA/tree. Supply FULL new-chat resume prompt INLINE in ONE complete fenced block plus canonical GitHub handoff/commit links; END current chat and recommend a new chat. No background execution or exact context-% claims.

NEXT MILESTONE: independent static review of the Windows root/ACL/handle candidate, then source-only secure state creation, exclusive encrypted journal and durable interrupted-recovery implementation; no protected hold lifted.
