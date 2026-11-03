# Vres-OS — 2026-11-03 M2 + #167 integrated Windows R1 script parser correction

**Evidence verdict:** ORIGINAL_INTEGRATED_WINDOWS_ATTEMPT=NOT_RUN (PowerShell 5.1 PARSER_ERROR before script block execution). GitHub integrated SOURCE unchanged; selected pytest, release-input validation, HEAD/tree/worktree preflight, environment restoration and native Windows owner ACL **NOT_RUN** under this attempt. Current corrected R1 Windows test **NOT_RUN**. No Claude, PostgreSQL, credential, installed-P2 or real legacy action was taken by this failure.

**Repo:** https://github.com/vosser24/Vres-OS
**Canonical docs branch:** docs/chatgpt-continuity-20261023. Prior current docs HEAD **9eb8773d99d3f2e76fd259b460de5f7338ab45e3**, tree **e8aa28bcf60a828e20a334e696ec93c5bddbb10f**. Reverify actual newest branch/index before new actions.

## 1. Exact original operator error and root cause

User pasted a complete integrated `& { ... }` PowerShell script block and reported after the closing brace:

```text
At line:40 char:48
+   if($observed -cne $expected){throw "MISMATCH $label: $observed != $ ...
+                                                ~~~~~~~
Variable reference is not valid. ':' was not followed by a valid variable name character.
FullyQualifiedErrorId : InvalidVariableReferenceWithDrive
PS C:\\Users\\User>
```

PowerShell variable-expansion syntax treats `$label:` in a double-quoted string as a malformed scoped/drive variable reference, so parsing fails before the compound script block begins. The user did **NOT** report preflight PASS, pytest results or any current Windows filesystem changes; this parse error means the compound body did NOT execute. The originally suggested full block had Git blob **53e51b031d0db0433aff0fc17c8f66094b178728**, file `docs/handoffs/VRES-2026-11-03-M2-167-INTEGRATED-SOURCE-OFFLINE-WINDOWS-GATE.ps1`. Keep it unchanged as ORIGINAL REJECTED operator script, not a PASS, not a performed integration test.

## 2. One-line PS5.1 interpolation correction — separate archived R1 script

Corrected only **one line** of the PowerShell script's `Expect` function, with all 17 pinned Git blobs, branch/ref, HEAD/tree, seven-path allowlist, py launcher, selected tests, isolated AppData, environment restore and final marker unchanged.

```powershell
# ORIGINAL REJECTED
if($observed -cne $expected){throw "MISMATCH $label: $observed != $expected"}
# R1 CORRECTED
if($observed -cne $expected){throw "MISMATCH ${label}: $observed != $expected"}
```

New R1 complete 181-line PowerShell operator script:

`docs/handoffs/VRES-2026-11-03-M2-167-INTEGRATED-SOURCE-OFFLINE-WINDOWS-GATE-R1.ps1`

**R1 script Git blob:** **11ca2355235bde1b8f1f3512c5e7ec0a616991e1**.

Generated directly from the previous pinned script by exact one-line replacement; GitHub create_blob SHA for corrected bytes verified, no other replacements. A static scan found no remaining ordinary `$name:` interpolations (besides valid `$env:` syntax) and no unsupported Windows PowerShell 5.1 `Tee-Object -Encoding` parameter. **PowerShell parser/execution NOT_RUN in the development container (PowerShell unavailable)**. This is a verified source edit, not Windows acceptance. The prior uncommitted prepublication `Tee-Object -Encoding` draft (blob f3dd468971422a14cbbec89c51ca12eef5bf2638) and its corrected original blob 53e51... remain historical; do not silently merge the separate issues.

## 3. Pinned integrated source unaffected

- Feature branch: `feature/personal-m2-167-offline-integrated-release-20261103`.
- Source HEAD **7a1d2da36f9ef1475e7909ca8850b9b641380b1d**, tree **98658c0270b65032f38ab38c0671c48b2a291bc1**, sole parent accepted M2 rollback **a65215a3b8b91ad4ab374c928ae3cf667e5b0f95**.
- Exactly seven intended source/test paths compared to M2-HOST: M install.ps1, M src/vres_os/install_recovery.py, A tests/test_install_rollback_proof.py, A src/vres_os/personal_data_sources.py, A src/vres_os/personal_data_source_store.py, A tests/test_personal_data_sources.py, A tests/test_personal_data_source_store.py. No new product code/test commits in response to the PowerShell interpolation problem. No product main merge; last main **9a8acc5d464b96432a93cb95daa9581412fb07ee** tree **659d3fdd6e635dbaecbd5c492ba7279754edaec7**.
- Original protected Windows installed P2 last observed release source **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, tree **205c081277ece483c634e1c801c39595abd4549c**, NOT freshly inspected by ChatGPT. Original P2 test-anchor path `C:\\Projects\\Vres-P2F-Postinstall-Hardening-20261022` protected. The new integrated test worktree path `C:\\Projects\\Vres-Review-M2-167-Integrated-20261103` may be created by the R1 script; it was NOT created by this parser-failed attempt, based on the reported syntax failure, but its current filesystem existence is NOT independently visible to ChatGPT.

## 4. What to do next, without protected actions

The user must run the NEW R1 complete script as one atomic block in normal Windows PowerShell 5.1, outside Claude Code, and capture native pytest output. Use fresh transcript if desired, but the script itself writes native `integrated-pytest-full.txt` and `release-inputs.txt` into a new isolated temp directory. Do NOT re-run the original parser-invalid script or delete any existing test worktree. If a worktree already exists, stop on the fail-closed path condition rather than overwriting it. Require original P2 anchor/official GitHub/HEAD/tree/sole parent/seven-source allowlist/17 PRE+POST blobs PASS, release-input verification exit0 (migrations 001–041, reject schema-048/experimental), combined native pytest exit0 with actual passed/failed/skipped case counts, env restoration and clean checkout. Keep actual FAIL evidence and source branches intact if it fails. **R1 is currently Windows NOT_RUN.** Do not run actual install.ps1, Vres CLI/doctor, native Claude or PostgreSQL.

Previously separately accepted M2 offline selected PowerShell result **EXIT0 with pytest roster missing**, and separately accepted #167 store offline selected PowerShell **EXIT0 with roster missing**, remain recorded at their original SHAs. Original rejected #167 source Windows 43 PASS/1 FAIL/exit1 preserved; corrected #167 R1 44 named PASS/exit0. Source integration cannot be called accepted merely because the separate source branches passed.

## 5. Binding absolute holds and full product plan

**LIVE_SCHEMA_048_INCIDENT=OPEN**: NO PostgreSQL even SELECT by any direct or indirect route, including CLI, hooks, installed runtime, doctor, migrations and offline release test side effects. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**: seven historical Claude Code posttool DB-route attempts, no ordinary native Claude Code or installed hooks. Independent F1/Fable trusted-positive protected-high authority NOT granted. No installed P2, current-user profile/credentials/PRISM/global Claude, real legacy project, Chairman/model/validator policy changes, product main PR/merge, or go-live without separate applicable P3 clearance and specific user P2 consent.

Preserve all V-01..V-42 original PERSONAL one-Windows-user daily-operations requirements, practical M0–M8 roadmap, #165–170/#174/#176, historical original rejected A12 18 PASS/1 FAIL, A13 28 PASS/1 FAIL, A16 environment-copy proof ambiguity, A19 blocked/uncommitted, PT1/PT2A–D, Hook-R1, Stage1–6/E7/E8/C2B/R0/F2, and original protected worktrees. After accepted integrated offline source, resolve host/DB incident holds separately, seek exactly scoped owner-approved installed release, run functional Chairman/task/project, Visual Studio/legacy and personal daily pilot. Do not invent Windows tests or a background job.

**Auto-checkpoint:** at/before 20 completed replies or conservatively approaching >50% context, verify GitHub source/docs refs, publish authorized completed changes with non-force expected-SHA and readback, full dated docs/handoffs + newest READ FIRST, one complete inline fresh-chat resume prompt, and stop with a recommendation to start a new chat. Context percentage and inaccessible Windows changes cannot be asserted precisely.
