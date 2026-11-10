# Vres-OS — 2026-11-10 Owner-reported Windows result-history 8/8 synthetic UAT, exact-context replay
**Record scope:** An owner-pasted Windows CMD transcript, checked against the authoring runner copy and live GitHub source. A ChatGPT session did not execute code on Windows or independently inspect the user's host.

## Result — owner-reported PASS, bounded to new feature
The owner reports running:
```cmd
py -3.12 -I -S -B "C:\Projects\vres_windows_result_history_uat_20261110.py" --approve-new-disposable-test
echo %ERRORLEVEL%
```
The displayed output reports pinned feature commit `04808884f27b9db722bc529e927962c36654488a`, full Git TREE `3c4976aacb799c08d86b1fa1db4e4572fd98a5d2`, source package TREE `36387294715f698e2fdfd04d231316fee58d72ab`, and `PASS verified full Git tree, package tree and pinned source blobs`. One public source ZIP was used, with owner-reported downloaded ZIP SHA-256 `c108140b8fdc94208425ea4397d058e201ce975f3cd839eaa8cc27f5f04dd983`.

**NEW disposable evidence directory (preserve; do not auto-clean):** `C:\Projects\Vres-ResultHistory-UAT-vznzvhwd`. It is distinct from the previous 7/7 Work Finish UAT folder `C:\Projects\Vres-WorkFinish-UAT-bnxteoxp`.

Owner-reported printed checkpoints:
1. `PASS 1/8 synthetic selected task and real document hashed`
2. `PASS 2/8 user confirmation gate refused unsafe completion`
3. `PASS 3/8 confirmed work completion saved original task and result link`
4. `PASS 4/8 original history retains token and hides document location`
5. `PASS 5/8 explicit path reveal displays saved document location`
6. `PASS 6/8 original note/receipt unchanged; one sidecar only`
7. `PASS 7/8 explicit reopen and exact-context document replay`
8. `PASS 8/8 changed document refused; historical record not called current`

End markers: `VRES_RESULT_HISTORY_WINDOWS_UAT_PASS` and `TEST_RUNNER_EXIT=0`; after the program exited, the owner separately entered `echo %ERRORLEVEL%` and the actual CMD printed **`0`**. This resolves the earlier parent Windows trial caveat where an independent shell exit was not echoed. Only the **new** UAT is claimed to have Windows 8/8.

## Runner inspection and provenance
A current Linux session inspected the exact assistant-authored runner at `/mnt/data/vres_windows_result_history_uat_20261110.py`, length **15,570 bytes**, SHA-256 **`af9e23135113098295cf51a3a20abde44e1c39806ea8b42cd754752c57c9f937`**. It pins the repository commit, full Git tree, source-only tree, four source blob IDs, requires Windows non-admin Python 3.12 isolated/no-site/no-bytecode flags and the explicit approval argument, creates one unique directory under `C:\Projects`, bounds archive size/member count/extraction, validates Git-compatible SHA-1 trees and source blobs before extracting Python into its own new directory, blocks socket/process actions after download, then exercises the existing source API/CLI with synthetic data. The inspected runner's exact PASS strings and source identities agree with owner-reported output.

**Limits:** Windows runner bytes were not independently hashed on the Windows machine; matching transcript does not cryptographically prove that host copy equals the inspected Linux runner. Downloaded ZIP bytes and Windows host attestation were not available in this session; their digest/tree checks are *runner-reported*. Prior separately required independent external static reviewer signoff is NOT_VERIFIED from this message. Nothing in this report asserts a full suite, source security audit, independent F1/Fable positive authority, production quality of the document, installed release acceptance or live task authority. This is a focused synthetic functional demonstration.

## GitHub continuity observed in read-only queries before this documentation record
Repository `vosser24/Vres-OS` (reported repository ID 1368577038).
- Docs `docs/chatgpt-continuity-20261023` HEAD `a501e2ffdf606090e787d56c18a3976f471a3570`; previous continuity recorded its TREE `cf1d19c5da91044766582f532eaeae72bde0ab29`, sole parent `61e93e5d37b27a42ed4815d8b5c57c240f6c52cf`. Connector rechecked current HEAD and one-commit-ahead comparison, but raw commit tree/parent headers were not exposed independently.
- Source `feature/personal-work-result-history-link-20261110` HEAD `04808884f27b9db722bc529e927962c36654488a`, source tree `36387294715f698e2fdfd04d231316fee58d72ab`, sole parent `258467ad0465f706c993444175efdaca026769fb`; live compare one ahead/zero behind, exactly five source/test paths. The original Git full TREE was verified by the owner runner, not independently from raw commit metadata in this session.
- Product `main` unchanged HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`.
- Protected R13 `feature/personal-w4-r13-universal-staging-hold-20261106` unchanged HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`.
- Historical installed P2 source identity `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`; **physical installed identity NOT_REVERIFIED**.

This evidence does not alter the existing product source. The earlier focused Linux 35 PASS across five runs and the previous parent-feature owner Windows 7/7 PASS remain distinct historical observations; no aggregate/suite acceptance is claimed. Prior harness failures and rejected attempts retained in earlier canonical handoffs.

## Scope, protected work and absolute holds
Vres-OS is one production-quality practical **personal** Windows daily-operations application for one user. Preserve original Chairman/task/memory/credential/project-adoption/release owners and all V-01..V-42, M0..M8; issues #163/#164/#165–170/#174/#176/#185; W0–W3 and W4 R1–R13 and original rejected evidence. Do not create duplicate task/memory/evidence stores or enterprise IAM/multitenancy.

`LIVE_SCHEMA_048_INCIDENT=OPEN` — **NO PostgreSQL, including SELECT**, directly or indirectly.
`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — **NO ordinary native Claude Code / installed hook execution**.
Original P3 incident OPEN; independent F1/Fable positive authority NOT_GRANTED; R13 universal release hold ACTIVE. NO protected installed P2 changes, actual original Task Day 01, real legacy project, user profile, real credentials, installer, migration, destructive rollback, Git for Windows maintenance action, main merge or product source revision. #169 installed Visual Studio UAT and #170 live personal pilot remain NOT_RUN.

## Next exact practical milestone
Windows **synthetic new-history-link** gate is satisfied as owner-reported 8/8 with independently echoed exit 0, under the precise scope above. Next is a **single useful owner-selected personal task-and-document trial only after explicit separate consent and scope selection**, in a new ordinary *non-legacy, non-sensitive* workspace with no installed P2/PG/native-Claude/real credentials. First prepare one concise approval boundary identifying the task and disposable/new project/directory, no automatic execution, no broad retest treadmill. Any real installed personal pilot remains BLOCKED by the open incidents and separate user consent requirements. Preserve evidence directories.
