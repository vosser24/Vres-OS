# Vres-OS — 2026-10-30 M2-HOST source candidate: personal upgrade must not provision prerequisites or mutate User PATH

**Status:** SOURCE_COMMITTED_GITHUB_REMOTE_VERIFIED; new Windows pytest NOT_RUN, real installer NOT_RUN, native Claude NOT_RUN, PostgreSQL NEVER CONTACTED BY THIS SESSION. This is a **single-user Windows application**, not an enterprise approval system. No installation authority is implied.

## 1. Read-first and exact refs

Start from the actual latest docs/chatgpt-continuity-20261023 HEAD, docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, accepted M1 Windows 110-PASS report, original Stage6 provenance and binding PERSONAL charter/M0–M8 plan. Previous canonical docs HEAD at this update's beginning: **b331b392b5eeb3ce42d75426da5fe33eb94e995a**, tree **4ee45f05174a52ec5827c816206991b348d2ee0e** (latest new docs SHA must be verified from remote after publication).

**Product main** 9a8acc5d464b96432a93cb95daa9581412fb07ee (unchanged). **Historically installed P2** 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c / tree 205c081277ece483c634e1c801c39595abd4549c; current Windows installation has NOT been freshly observed. **A18 accepted** 7bace7758e5c7f9a00f26179eb741ef3a319bc77 / tree 4d17344a9510de6394840092cf33729ab153fbb5, historical 49 selected Windows PASS. **M1 accepted bounded offline source** 28120eb49b6b950c7402455db19dcbdcf6d991a6 / tree 815fce697f16509bae150729891738d879d6ca9c, 110 distinct Windows PASS, successfully staged 207 files and rolled back synthetic previous P2 plugin/launcher/Claude files; no real installation. Uploaded M1 log omitted original preflight console and separate direct exit-code echoes; preserved as a limitation.

**NEW M2-HOST feature:** feature/personal-m2-host-update-no-prereq-path-mutation-20261030.
**HEAD:** 526fb9d61e4a61c26c19931f9adf2d68eecd1bc8.
**TREE:** 9919f363a8608e31e4c5a6f66adb765c7021b484.
**ONLY PARENT:** accepted M1 28120eb49b6b950c7402455db19dcbdcf6d991a6.
**Source link:** https://github.com/vosser24/Vres-OS/commit/526fb9d61e4a61c26c19931f9adf2d68eecd1bc8
Exact two changed paths verified GitHub compare, Git blob readback:
- M install.ps1 blob **d52ab1c2f5d81c44d53026c09e426ea4f18571c5**, +21/-2;
- M tests/test_install_contract.py blob **62310e3ff6af2f9a8f49f310bb32ffea45e53752**, +38.

All accepted M1 source, migration inputs, hook manifest, install_recovery.py, original P2 release bytes, Chairman/model policy, credentials, projects, database boundary, source-read protections, and product main are unchanged. The GitHub feature was created from exact M1 parent, committed as one tree, published with nonforce expected-old-SHA and verified by remote readback.

## 2. Concrete M2-HOST installer source analysis — why this increment

The original install.ps1 (still committed in M1) unconditionally treated an update like a fresh dependency setup: missing Git/Claude triggers winget; missing Python triggers winget; PostgreSQL command/service absence may prompt winget installation; optional Codex may trigger npm global install. It also could proceed with Update even if the target had no active pointer, and rewrote the current-user registry PATH to include Vres bin after other mutations. Existing interrupted-install recovery v2 snapshots the plugin, pointer, launchers and Claude files, **but not the Windows user PATH or winget/npm prerequisite installations**.

These are meaningful real personal-user upgrade and rollback risks. M2 scope is limited to the **-Update maintenance branch**, not changing first-install behavior or inventing a new installer/rollback authority:

1. **Refuse ambiguous fresh-versus-update:** before external prereq calls or managed install directory creation, Update requires existing active-install.json leaf and installed Vres plugin directory. Existing Assert-Managed still checks ownership.
2. **Refuse external provision during an update:** missing Git, Claude or compatible Python now reports a STOP instead of invoking winget; requested optional Codex that is absent STOPs instead of npm/global installation.
3. **Do not inspect or provision PostgreSQL in update mode:** local psql/Get-Service/winget branch applies only to non-Update initial installation. This is a source control, **not proof of physical no-contact** elsewhere.
4. **Preserve current-user PATH during updates:** if the Vres bin entry is missing, warn that separately approved repair may be needed; do not mutate the PATH since rollback v2 cannot restore it. Initial fresh-install PATH handling remains unchanged and is NOT production-certified.
5. **Keep existing approved update confirmation, pinned source staging and read-back, exact plugin snapshot/recovery, user-scoped launcher installation, and all original functionality.** Do not bypass normal consent.
6. Three source-level test functions added to tests/test_install_contract.py cover existing P2 pointer/plugin requirement, missing external prerequisite paths including Postgres/Codex, and User PATH preservation. These tests are authored but NOT run in this session. Existing test_install_preflight.py tests should be run as an impacted regression module.

## 3. Hard operating holds — still OPEN, especially after M2 source change

**LIVE_SCHEMA_048_INCIDENT=OPEN — NO PostgreSQL even SELECT**, direct or via Vres CLI/MCP/bootstrap/doctor/migration/recovery/hooks/F2. Nothing about skipping installer PostgreSQL prerequisite checks clears this incident.

**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**, with seven historical native Claude post-Read/Grep DB-routing attempts refused. Stage3–5 narrowed installed P2 versus source A18 to exact three matcher-only differences (9→0 in-memory), Stage6 proved installed P2 manifest coherence; no Stage7 repeat. M2-HOST source does NOT eliminate existing installer calls to native claude --version, claude plugin list or claude plugin validate, nor does it independently prove managed/global/other-plugin/lifecycle behavior. **NEVER EXECUTE the real installer or normal native Claude while hold remains.**

No trusted F1-positive/Fable-high, Sonnet/high→Opus/medium model installation, credentials, real legacy projects, user-profile or installed P2 changes, PR/main merge or go-live without separate permission. No such permission is solicited by a GitHub-only source commit.

## 4. Next exact Windows action: one self-contained P1 offline test, not the installer

Archived ONE complete, source-SHA-pinned native Windows PowerShell script:
**docs/handoffs/VRES-PERSONAL-M2-HOST-UPDATE-OFFLINE-WINDOWS-SELECTED-TEST-2026-10-30.ps1**
Git blob **762366c260226a3a30caf8e1896402b6177888c1**.

Run outside Claude Code in a normal PowerShell 5.1 shell, copy the **entire** code block. It uses original P2 anchor **C:\Projects\Vres-P2F-Postinstall-Hardening-20261022** exact and clean, official GitHub origin, fetch M2 feature with Git hooks disabled, and creates NEW detached source checkout **C:\Projects\Vres-ChatGPT-Review-Personal-M2-Host-20261030** (refuses existing path). Verifies M2 exact HEAD/tree/M1 parent/P2 ancestry and exact TWO modified paths, Git diff --check, NINE pinned source/test/incident boundary blobs before and after. Scrubs/restores process-level PG/DB/integration/Claude/Python environment variables, private temporary AppData, and original directory. Executes ONLY one offline pytest command for the affected **tests/test_install_contract.py and tests/test_install_preflight.py** with plugin autoload disabled; prints TEST_EXIT_CODE, individual PASSED test names and postflight. No installer, pip, Claude executable/hook, database, credentials, user PATH manipulation, real project or installed P2 change is requested.

**M2_WINDOWS_SELECTED_TESTS=NOT_RUN** until complete operator console evidence (including preflight) is pasted and assessed. Preserve any original failure instead of claiming success; no rerun of M1 110 tests for paperwork. The last marker to evaluate is **VRES_PERSONAL_M2_HOST_WINDOWS_SELECTED_TEST_COMPLETE_PENDING_EVALUATION**. Process environment restoration must be observed and results cannot be guessed.

## 5. Next integrated milestone and user outcome

M2-HOST source's two-path protection alone does NOT authorize installed upgrade. After offline Windows acceptance, separately determine whether the original installer can safely launch Claude CLI under the host-hook hold and whether installation interruption/restoration semantics are adequate for actually protected current-user files. Prefer one coherently designed user-scoped release activation with tested rollback and explicit P2 approval; do not hotpatch P2 installed hooks or build another Stage7/A19/A20 serial matcher test. M2-DATABASE remains a **separate** incident with no SELECT until independently cleared and approved. There is no shortcut from source-only tests to a production claim.

The binding daily personal product path remains M3 Chairman/task/session and useful experience (#165/#176), M4 current-user Claude/PRISM and fresh/legacy adoption (#166/#168/#174), M5 secure same-Windows-user credential reuse / data source registry (#163/#164/#167), M6 Visual Studio real legacy acceptance (#169), M7 daily pilot/readiness (#170), optional M8. Preserve all V-01..V-42 functionality, P0/P1/P2/P3 methodology and proportional actual utility.

Original historical REJECTED A12 345a568b551ac23183c54f10611335adee903b96 (18PASS/1FAIL/exit1) and REJECTED A13 cdaa39aaa774cef88a4831bf6b157e380fbb69d9 (28PASS/1FAIL/exit1), corrected R1, A16 env-copy ambiguity, A19 source blocked/uncommitted, PT1/PT2A–D, Hook-R1, Stage1–6, E7/E8/F2/048, all protected worktrees and Git refs remain preserved. Closed historical source #163/#164/#174 do not mean live daily capability.

## 6. Continuity

Canonical index newest READ FIRST entry must link to this handoff and full script. Hard automatic checkpoint at/before 20 completed replies or conservatively estimated context >50%, whichever first: verify GitHub refs/trees, commit all authorized source/docs via nonforce exact SHA, seal dated docs/handoffs and index, give entire new-session resume prompt ONE inline fenced code block and recommend fresh chat. An M2 source commit and ordinary docs seal do not, on their own, mean the automatic checkpoint triggered.
