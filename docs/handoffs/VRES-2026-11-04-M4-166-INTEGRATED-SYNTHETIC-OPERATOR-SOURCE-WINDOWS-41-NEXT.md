# Vres-OS — 2026-11-04 M4 #166 integrated synthetic migration operator demo SOURCE PUBLISHED; Windows 41-case gate NEXT

**BOUNDARY: M4_166_INTEGRATED_SYNTHETIC_OPERATOR_SOURCE_PUBLISHED__WINDOWS_41_NOT_RUN.** One coherent P1 source bundle for a PERSONAL one-Windows-user Vres-OS, not enterprise multi-tenant identity or a live first-run release. This is not a real Claude/PRISM installation, real user-profile migration, native hook, credential operation, PostgreSQL action, protected F1/Fable approval, or live pilot.

## 1. GitHub canonical state and accepted exact source lineage

Repository: https://github.com/vosser24/Vres-OS
Canonical documentation branch: docs/chatgpt-continuity-20261023.
READ FIRST: docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md.
Documentation parent prior to this handoff: **HEAD e23e01d8acf6daeca03331595209e280f49bf2f6**, **TREE 177282eb293e11995c81eee08e8e90cd5783fb03**. Verify the new docs HEAD/TREE remotely AFTER the new docs commit; do not guess them here.
Product main unchanged, verified remote HEAD **9a8acc5d464b96432a93cb95daa9581412fb07ee**, TREE **659d3fdd6e635dbaecbd5c492ba7279754edaec7**. No main merge, no PR.
Prior accepted exact M4 KEEP/DROP source HEAD **ec54f7535aa29d7588c25e221f6bd2bae7a437c8**, TREE **d914c60169dc01c34b1cc987170cf66d66324bad**, 144 selected Windows PASS with user-uploaded evidence provenance limit. Its published branch remains **feature/personal-m4-global-legacy-migration-review-20261103**. Never relabel those historical tests as validation of the new source.

**New dedicated feature branch:** feature/personal-m4-integrated-synthetic-operator-dryrun-20261104.
**New exact published source HEAD:** **2b51b3aa9e4fe40fce53ffd457e1d5f218443209**.
**New source TREE:** **34072a722efe221042ddc922c5461c1a1c3192da**.
**SOLE source parent:** accepted M4 144-PASS source **ec54f7535aa29d7588c25e221f6bd2bae7a437c8**.
**Parent TREE:** **d914c60169dc01c34b1cc987170cf66d66324bad**.
Exactly TWO added files, no edits to accepted parent:
- A src/vres_os/global_claude_synthetic_operator.py — **Git blob 78695f60ba735eba83cea702a956ab9697922808**.
- A tests/test_global_claude_synthetic_operator.py — **Git blob 4721fde5f0645139aef4cd948d41445697b8c4fe**.

The full Python source and tests were locally written in ChatGPT's disposable Linux container and transferred to GitHub via the connected GitHub Git object API. GitHub blob SHAs exactly matched the **local git hash-object** values for both files. The new feature branch was created at the accepted parent; publication used **update_ref force=false, expected_sha=ec54f7535aa29d7588c25e221f6bd2bae7a437c8**, with independent remote ref/commit HEAD/tree/sole-parent readback verified. No alternate safety-control bypass, nonfastforward or main update.

## 2. Implemented P1 synthetic operator-facing bundle (NOT real adoption)

New module composes the accepted global adoption preview/transaction/review/disk-fixture interfaces, without introducing a new migration state engine or any host/user-profile API:
- Only **built-in fixed demo** governance bytes and an opaque in-memory native handle. Scenarios allowed: standard, changed, empty. Caller cannot provide a real file path, profile root, arbitrary raw bytes or credentials to this wrapper. Demo PRISM-like path strings are synthetic and are not an observed installed PRISM state.
- Preparation, sealed synthetic snapshot, self-owned TemporaryDirectory disk snapshot/quarantine/rollback; optional separately simulated interruption with fail-closed recovery and exact rollback.
- In-memory quarantine, sealed deterministic grouped numbered legacy governance review and human-readable recommendation explanation (heuristic, NOT real Chairman semantics).
- Textual interactive API-like view via render_synthetic_migration_dry_run; begin_synthetic_migration_dry_run returns a typed in-memory revision; record_synthetic_migration_choices processes KEEP/DROP numbers over multiple turns without changing previous in-memory revision; inspect_synthetic_migration_dry_run reports pending and chosen items, SHA identifiers, status and destinations; freeze_synthetic_migration_dry_run produces a synthetic plan only when all decisions are resolved; preview_synthetic_migration_rollback revalidates exact in-memory restoration and preserves the review state.
- Tampered or stale snapshot, review, sheet, disk evidence, scenario or claimed authority fails closed. Existing parent checks enforce syntax and duplicate choice denial.
- Every real activation, real user provenance, actual snapshot/hook quarantine, actual first Claude launch, secret use, F1/Fable validation and applied KEEP/DROP flag remains **FALSE**.
- No raw legacy byte material or opaque vendor state name in operator reports; only example filenames and recommendations. No installed Vres code or normal start_vres entrypoint wiring was changed.
- No persistent real operator approval or fork prevention: the session is only an in-memory demonstration. A Git SHA, content digest or synthetic proof does not create independent host/OS authority, power-loss durability, authenticated consent or approved physical recovery. On-disk writes are confined to self-created disposable temporary fixtures, not a real user profile.

## 3. Tests: provenance, failures and pending native Windows acceptance

**Source authoring check in ChatGPT Linux container:**
- New test module compilation and source module compilation PASS.
- First **isolated local stand-in** pytest run: **40 PASS / 1 FAIL** (the test-only local stand-in for the previously accepted migration-review API failed to reject one forged authority field). This was a stand-in incompatibility, not observed evidence of an actual GitHub-parent failure. Preserve the original 40/1 result.
- Corrected the LOCAL STAND-IN ONLY to mirror accepted strict parent decision-sheet field checking (real accepted parent source and new candidate bytes unchanged). Reran the focused new module and got **41 PASS / 0 FAIL** (pytest 9.0.2, Python 3.13.5, Linux). This exercised a stubbed public API compatible harness, **NOT the full accepted GitHub parent checkout** and **NOT Windows**. Do not present it as full-integration acceptance or native independent validator review.
- The exact checked local new module and test bytes were published with blob SHAs 78695f60... and 4721fde5....
- The test corpus covers readable grouped demo, roundtrip snapshot/quarantine/rollback, interrupt 0/1/6, empty/changed state, per-turn pending choices, frozen KEEP and DROP, exact SHA bindings, cross-snapshot, unauthorized/duplicate/malformed/prompt-injection choices, in-memory rollback and no real authority output.

**Next published docs test gate:** docs/handoffs/VRES-2026-11-04-M4-166-INTEGRATED-SYNTHETIC-OPERATOR-WINDOWS-41-OFFLINE-GATE.ps1, exact Git blob **81ae8827802c94858eb8fcee476a50b4716e58a4**.
**EXPECTED, NOT_RUN: 41 distinct Windows named PASS in ONLY tests/test_global_claude_synthetic_operator.py, exit code 0, 0 FAIL/ERROR/SKIP, process environment restored, full PRE and POST Git.** Do not automatically rerun accepted 144/125/254 suites for paperwork. If the new test file fails on actual accepted parent, preserve exact failure and correct it in a distinct source commit; do not alter parent or rewrite historical PASS.
- Run only in ordinary Windows PowerShell **5.1 OUTSIDE native Claude Code** with a hash-verified script. The earlier Windows script execution-policy and stream-merging NativeCommandError pitfalls are addressed by a separate child PowerShell process with Process-only execution policy and separate stdout/stderr capture, NOT merging stderr into Stop-enabled pipeline; do not alter permanent execution policy. Group Policy override is NOT authorized.
- Exact protected P2 Git checkout path: C:\Projects\Vres-P2F-Postinstall-Hardening-20261022, previously observed HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c / TREE 205c081277ece483c634e1c801c39595abd4549c. This is an original source checkout, not a fresh actual installed-release examination. Script verifies original P2 HEAD/TREE/clean and official GitHub origin, fetches the exact dedicated feature ref, verifies source SHA/TREE/sole parent/two A paths/two Git blobs, and creates a NEW protected DETACHED review checkout C:\Projects\Vres-Review-M4-Integrated-DryRun-20261104 only if that path is absent.
- Python test process receives disposable TEMP/TMP and current-user HOME/AppData substitutes, PG/DB/GIT/CLAUDE/PRISM/credential env scrubbing, disabled pytest plugin autoload, process-only environment restoration verification, complete named pytest output and protected source postflight.
- **Windows result on new source: NOT_RUN**. Full repository test suite: NOT_RUN. Actual installed/global/PRISM/legacy/PG physical test: NOT_RUN.
- Final expected marker: VRES_PERSONAL_M4_166_INTEGRATED_SYNTHETIC_OPERATOR_WINDOWS_41_POSTFLIGHT_COMPLETE_PENDING_EVALUATION. This is a future output marker, NOT evidence of a run.

## 4. Future product path — fewer integrated bundles, original roadmap intact

Keep the original M0–M8 roadmap and all original V-01..V-42; this is execution grouping only, NOT deleting or downgrading any requirement:
- **Bundle A: integrated safe onboarding** (#166 now synthetic dry-run source; #168 project intake) — verify one coherent user-first scenario, later real current-user only with P2/P3 clearance.
- **Bundle B: personal everyday-use candidate** — M1/M2 artifact/recovery source + M3 task/Chairman + essential #176 memory + #163/#164/#167 user-scoped resource handling + practical bounded output, one coherent disposable source-to-artifact gate.
- **Bundle C: separately controlled real installation safety** — resolve host-hook and schema-048 holds with acceptable independent evidence before native Claude/DB and explicit owner approvals; no implicit installer.
- **Bundle D: #169 physical Visual Studio/PRISM/real-project integration** after C clearance and specific owner consent, no premature PRISM installation.
- **Bundle E: #170 approved daily pilot and readiness** on a pinned installed release with honest held/enabled inventory and rollback evidence.
- M8 optional/experimental features remain backlog, never fabricated as DONE.

The original #166 issue remains OPEN for actual first-run onboarding, real approved review, deterministic state, real bounded profile snapshot, native hook quarantine, protected Fable clearance, recovery journal, idempotence. No source-only test closes it. Original #165 Opus/medium Chairman desired configuration remains uninstalled. Original #167 database catalog cannot contact PostgreSQL under the open incident. #168 project architecture planning remains protected by #174 requirements. #176 experience work remains tracked. #169 and #170 remain OPEN.

## 5. Absolute holds, protected works and original failures

- **LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT**, direct/indirect, no alternate target, query, bootstrap, CLI, MCP, F2, installed hooks, migrations or backups.
- **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code or installed managed hooks**, no direct independent Claude provider review. Preserve seven prior refused attempts, Stage1–6 source/host history and fixed matcher release distinction.
- **Independent trusted F1/Fable positive authority NOT GRANTED**. No fake protected signature, static approved state, fake Chairman judgment or policy override.
- No real ~/.claude/PRISM user profile, credentials/Locker, real legacy project, installed release overwrite or main merge/PR/pilot without separately cleared applicable P3 incident and specific owner P2 consent.
- Original installed P2 source HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c/TREE 205c081277ece483c634e1c801c39595abd4549c are HISTORICALLY observed; not re-inspected physical installation by GitHub tools. All prior Windows detached/protected worktrees must remain intact.
- Historical selected Windows results: M2+#167 254 PASS / 3 symlink-privilege SKIP; M3 session 14 PASS; M3 Chairman briefing 52 PASS; M4 preview 46 PASS; M4 in-memory fixture 93 PASS; M4 disposable disk 125 PASS (partial initial PRE supplied), M4 migration review 144 PASS (full reported PRE/POST, operator-upload provenance limit). Tests belong to exact earlier source commits only.
- Preserve original rejected authoring attempts 50PASS/1FAIL and mismatched make_fixture import (rejected test blob a18cdc6e0e84685d61a759f6901dd800337397d8), blocked original GitHub update, rejected Windows default execution-policy and first stderr-merging launch; this new P1 author's local 40PASS/1FAIL stand-in mismatch; all PT branches and known P3 incidents, protected worktrees, source/test SHAs, complete V-01..V-42 requirement register and M0–M8 roadmap.
- Original requirement register docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md; 42-row personal board docs/roadmap/VRES-PERSONAL-LOCAL-WINDOWS-ACCEPTANCE-AND-FULL-DEVELOPMENT-BOARD-2026-10-31.md; roadmap docs/roadmap/VRES-PERSONAL-DAILY-OPERATIONS-DELIVERY-PLAN-2026-10-30.md and binding charter docs/architecture/VRES-PERSONAL-SINGLE-USER-PRODUCT-CHARTER-AND-METHOD-2026-10-30.md. Treat obsolete immediate operator instructions in historical sections as historical only.

## 6. Exact next operation and checkpoint

**NEXT:** Execute ONE expected-41-case selected offline Windows gate for published new exact source in an ordinary PowerShell 5.1 child OUTSIDE Claude Code. Demand complete initial PRE, named pytest, environment-restore and POST transcript, actual exit and separate stderr. Evaluate factual results; commit acceptance/failure docs with honest provenance. No real current-user Claude/PRISM/DB tests. If even one test fails, record and fix the exact defect in a distinct corrective commit; do not silently waive the failure, delete worktrees or rerun unrelated suites.

**PROJECT HARD CHECKPOINT:** At or before 20 completed assistant replies since last verified checkpoint OR conservative >50% context, whichever first (checkpoint early when uncertain), stop starting phases, reverify docs/main/current feature branches, exact HEAD/TREE/PARENTS, actual installation only if accessible/authorized, publish authorized GitHub source/tests/docs with nonforce exact expected SHA and readback, create dated continuity handoff and newest READ FIRST index, preserve PASS/FAIL/NOT_RUN provenance, original rejected attempts and P3 holds, give full inline one-block fresh-chat prompt and links, end session and recommend new ChatGPT chat. Never infer unpushed local Windows files or promise background work.
