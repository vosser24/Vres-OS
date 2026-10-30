# Vres-OS PERSONAL — Stage 5 matched-hook in-memory simulation PASS, Stage 6 release-provenance read-only NEXT

**Recorded:** 2026-10-30, Europe/Athens. **Repo:** vosser24/Vres-OS. **Evidence:** operator's complete-looking pasted ordinary Windows PowerShell Stage 5 stdout, not original byte-attested stdout, hook execution trace or SQL packet proof.

## 1. Stage 5 completed and accepted only for in-memory simulation

**STAGE5_IN_MEMORY_DRY_RUN_ACCEPTED.** Operator ran Stage 5 SHA-pinned read-only PowerShell script, Git blob **d3ff2d600f14a7003115a08818618dc83d920fe1**. The exact-source and exact-installed SHA256 checks passed, and both manifest files remained unchanged on disk. Stage 5 output confirmed:

- Accepted A18 source manifest (8286 bytes): SHA256 **88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2**.
- Installed user-scoped Vres skills manifest (7921 bytes): SHA256 **700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7**.
- **Nine** static installed Read/Glob/Grep post-hook matches before simulation, from one PostToolUse command + one PostToolUse MCP and one PostToolUseFailure MCP per builtin read tool. These are static match counts, not observed executions.
- Exactly three installed matcher properties **replaced IN MEMORY**: PostToolUse groups **2**, **4**, and PostToolUseFailure group **1**. No other parsed hook group fields modified.
- **All 17 aligned groups and all non-matcher payloads preserved**. Full in-memory simulated manifest structurally equals accepted A18 source. **30** sampled source-versus-simulated event/tool comparisons equal. Read/Glob/Grep post-hook match count reduced **9 to 0**.
- Both on-disk SHA256 identities unchanged. Console reported **IN_MEMORY_SIMULATION_ONLY=TRUE**, **BACKUP_CREATED=FALSE**, **ROLLBACK_TESTED=FALSE**, **INSTALLED_REMEDIATION_AUTHORIZED=FALSE**, **EFFECTIVE_RUNTIME_HOOK_SAFETY=NOT_ESTABLISHED**, and completion marker **VRES_HOST_HOOK_STAGE5_IN_MEMORY_DRY_RUN_COMPLETE**.

**Important restriction:** Stage 5 established a narrow static fix candidate, but no backup, rollback exercise, installed repair, Claude Code invocation, hook execution, safe native-code review, no-PostgreSQL packet attestation or incident clearance. Do not translate this result into permission to change installed hooks.

## 2. Next concern: release integrity if installed hooks are patched

Read-only GitHub source inspection at accepted A18 reveals the Windows installer's source at install.ps1 git blob **29a5f0da235021cc8c5607eb92218e5ea98145fa** and release_artifact.py git blob **ddfc1beacad98199b489dc6f56456baf4d519c6a**. During installation the installer:

- Stages the approved source into a release directory, retaining release-manifest.json with Git source commit, tree, individual file blob IDs and SHA256 values.
- Creates the staged Vres plugin under the release's distribution/vres-os directory and validates the installed plugin against the same source manifest using verify-tree, including the installed hooks file.
- Writes current-user active-install.json with release ID and plugin path; later installed integrity tools can compare plugin bytes against that pinned release identity.

**Consequently:** replacing three matcher strings in the installed hooks file MAY cause a source-integrity mismatch with its existing release-manifest.json. An unreviewed hot-patch or updating only the installed manifest would be unacceptable: the first can silently invalidate release identity and the second can rewrite audit evidence. Do not infer the current installed release's exact SHA/manifest condition from source alone. Inspect the actual pinned current-user release record next.

## 3. One next exact operator action: Stage 6 local release provenance inspection

Full **strictly read-only** PowerShell script: **docs/handoffs/VRES-HOST-HOOK-STAGE6-RELEASE-PROVENANCE-READONLY-2026-10-30.ps1**, Git blob **9fcc0469e7d49c2d7998ecceb74e69dffd0e171f**, **137 lines**. Supply the WHOLE script as ONE INLINE PowerShell block, not a file-only instruction. Run in ordinary Windows PowerShell, never Claude Code.

Stage 6 pins and checks SHA256 of the current-user active-install.json **33D775BBDEE13FE0B4C8552B1DA24C29DDFB20B502B298014F0501BBD9263A59**, installed hooks **700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7**, and accepted A18 hooks **88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2**. Parse only active pointer release ID and plugin_path; validate expected exact current-user root and a restricted release ID shape without displaying other metadata. Read bounded local release-manifest.json and staged distribution/vres-os/hooks/hooks.json. Check precisely one manifest entry for plugins/vres-os/hooks/hooks.json, compare stored SHA256 with staged and installed actual SHA256, output release source commit/tree, release hook Git blob and hashes, and re-check all five local file hashes remain unchanged. It rejects UNC/reparse paths, missing/oversize files, invalid pointers or mismatches, without invoking any hook, model, installer or database.

**Expected success:** VRES_HOST_HOOK_STAGE6_RELEASE_PROVENANCE_READONLY_COMPLETE and PASS: ALL_FIVE_ON_DISK_FILE_HASHES_UNCHANGED. If staged and installed match the recorded release, the script reports SINGLE_FILE_MATCHER_PATCH_WOULD_DIVERGE_RELEASE_MANIFEST=TRUE. This is a safety finding, not an instruction to perform the patch. If it finds release drift, STOP and preserve full console; do not repair, rewrite manifests or modify evidence.

Stage 6 is not proof that a backup/rollback procedure works; it neither creates a backup nor performs recovery. After Stage 6 evidence, design a **separate explicit user-approved** atomic remediation with integrity-aware verification and independently tested rollback before any installed change. Avoid normal install.ps1 or Claude Code because these can execute Claude and potentially indirect held integrations.

## 4. Hard holds and full continuity

**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**: seven earlier native Claude Read/Grep automatic posttool database routing attempts were refused. **LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL EVEN SELECT**, including Vres MCP/CLI/hooks/bootstrap/doctor/recovery/F2 or direct driver. Neither Stage 5 nor Stage 6 can certify effective managed/installed/lifecycle/other-plugin hook behavior or clear these incidents. No native Claude Code review, installed/global Vres/Claude/PRISM change, credential modification, positive F1/Fable-high issuance, real Visual Studio legacy project activation, main PR/merge or production release.

A18 remains latest selected Windows-accepted source HEAD **7bace7758e5c7f9a00f26179eb741ef3a319bc77**, tree **4d17344a9510de6394840092cf33729ab153fbb5**, 49 PASS, 33 pre/post SHA-pinned Git blobs and verified process environment restoration. A19 separate state-directory ancestor hardening writes were blocked by automated safeguards: **NOT committed**, not Windows-tested. Retain original A12 Windows 18PASS/1FAIL and A13 28PASS/1FAIL rejections and original pristine worktrees; A16 23 PASS with separate environment-restoration script-copy caveat.

Preserve PERSONAL P0-P3, PT1/PT2A-D, Hook-R1, #168 A1-A18, full V-01..V-42, #165-170, #174, #176 E7/E8, #166 global Claude/PRISM, #167 single-user Data Source Registry/credential reuse, #169 real Visual Studio legacy onboarding and #170 readiness/go-live. Stage 6 remains strictly read-only until additional explicit authorization.
