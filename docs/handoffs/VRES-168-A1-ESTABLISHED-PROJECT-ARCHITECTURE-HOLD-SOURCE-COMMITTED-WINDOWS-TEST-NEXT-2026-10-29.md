# Vres-OS — #168 PERSONAL 168-A1 established-project architecture hold, SOURCE COMMITTED; guarded Windows tests next

**Date:** 2026-10-29 Europe/Athens. **Repository:** vosser24/Vres-OS.

**CURRENT:** V30_168_A1_OFFLINE_SOURCE_CANDIDATE_COMMITTED / GITHUB_THREE_PATH_ALLOWLIST_VERIFIED / WINDOWS_SELECTED_TEST_NOT_RUN / INDEPENDENT_CLAUDE_REVIEW_NOT_RUN / NO_PROJECT_OR_INSTALLED_HOOK_WRITES / NO_POSTGRESQL_CONTACT / NO_PROTECTED_FABLE_VALIDATION / NO_ACTIVATION_AUTHORITY.

## 1. Why this is the next material functional increment

The full V-01..V-42 functionality register and the ChatGPT-led full-scope October 22 delivery plan remain binding; #168 "Project adoption and canonical Claude scaffold" is OPEN/PARTIAL. The accepted P2-D module already implements fresh-project scaffold, legacy Claude-surface inventory, secret-safe snapshot, numbered KEEP/DROP, operator decisions, activation journaling, interrupted recovery and rollback. Do NOT rebuild those.

**Reproduced source-level gap:** src/vres_os/project_adoption.py START previously treated **any project with zero existing Claude surfaces** as fresh, immediately wrote root CLAUDE.md, and changed state to active, even if a substantial Python/JavaScript/.NET codebase was already present. That skipped the existing independently accepted #174 architecture auditor's established-project alignment-plan requirement and Fable/high protected validator hold. This is a real V-30 fail-open readiness classification, not another speculative planning contract.

**Bounded current fix:** when a project has no Claude surface, reuse existing src/vres_os/architecture_governance.py audit_project(root) BEFORE writing project CLAUDE.md. If its static evidence says established project alignment is required OR inventory scan was incomplete, durably record **architecture_review_required**, audit digest, detected architecture profiles, plan status NOT_SUBMITTED, completeness count and required Fable/high validator in the Vres **separate state root**, return changed=False, and do NOT write project files or activate. A genuinely fresh project with a complete audit continues to get only the original single scaffold and active state. A repeat call with unchanged audit is idempotent; structural changes cause a new diagnostic audit digest (not a Git identity). The existing project-adoption decide/activate path rejects this new state because it requires awaiting_operator; no fake Fable approval or user consent can bypass it.

The existing bootstrap.start_for_project(project_root) now recognizes architecture_review_required as PROJECT_REVIEW_REQUIRED, returns only bounded diagnostic architecture context and an explicit read-only audit / incremental plan / separate Fable-high validation action, BEFORE reaching ConfigStore setup, migration or Repository project creation. Other bootstrap paths unchanged.

**Important limitations:** This is the first fail-closed established-without-Claude classification gate. It does **not** implement drafting/changing the architecture alignment plan, obtaining Fable/high acceptance, advancing architecture_review_required to an activated state, full #166 global Claude adoption, #167 DB registry, existing legacy-with-Claude plan enforcement, or real #169 Visual Studio acceptance. It does not change already-active project records or the installed Vres release. An audit digest is structural diagnostic evidence, NOT canonical source SHA, installed-state proof, plan acceptance, trusted issuer or installation permission.

## 2. Immutable GitHub feature evidence

**Branch:** feature/168-personal-established-project-architecture-gate-20261029
**Published source HEAD:** **2a21431d440632e09f2bc5e155aa27a47ecdfa98**
**Published source tree:** **bb5b16fc71d55f9d2030cc250df93c03e76f8ebe**
**Sole direct parent:** HOOK-R1 Windows-tested HEAD **891fb22287b6ee8b028eda7256c0b5639df40c04**, tree **1b9d7ddcc4f6c8e0cafda8cea5e1c5d51e3ca9db**.

GitHub nonforced expected-old branch update, commit/tree/parent/ref readback, compare one commit ahead/zero behind and EXACT THREE changed paths PASS:
1. MODIFY src/vres_os/project_adoption.py from **b191318d48d6866befa530c3ac80c1f8824042cb** to Git blob **5d6988cd13471a3012ee407327d0d82974062ed3** (new source length 775 LF lines).
2. MODIFY src/vres_os/bootstrap.py from **44c3082c4ec8cf936e10b8090c00577885893313** to blob **c326842ac936e70a0c3d238578942759ae68aff9** (655 LF lines).
3. ADD tests/test_project_adoption_architecture_gate.py blob **9d95b63c29773084aa9ecf780f2f6dabead2d089** (220 LF lines, eight new focused test functions).

All original #174 architecture policy/plan/auditor files, existing 724-line P2-D tests, 547-line architecture-governance tests, protected tests/conftest.py, Chairman and Hook-R1 manifest remain byte-identical. No change to remote product main, installed user Claude, existing real project, credential store, PostgreSQL, any model or protected validator.

## 3. Exact next operator Windows validation, and acceptance limits

**Proposed one-atomic 166-line Windows source checkout/test script:**
docs/handoffs/VRES-168-A1-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-29.ps1 — Git blob **936a6d0b52ab4bd727b0b7a0c269bafbb750f7fc**. Include the COMPLETE literal PowerShell block INLINE in the ChatGPT response (not only file link). DO NOT run via Claude Code or execute from installed Vres CLI.

Script checks:
- Original personal P2 source anchor **C:\Projects\Vres-P2F-Postinstall-Hardening-20261022**, expected HEAD **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, clean.
- Prior successfully tested Hook-R1 worktree **C:\Projects\Vres-ChatGPT-Review-Personal-HOOK-R1-20261029**, HEAD **891fb22287b6ee8b028eda7256c0b5639df40c04**, tree **1b9d7ddcc4f6c8e0cafda8cea5e1c5d51e3ca9db**, clean.
- Fresh destination **C:\Projects\Vres-ChatGPT-Review-168-Architecture-Gate-20261029** absent before action; official origin, exact remote feature SHA, fetch, create NEW detached checkout at **2a21431...**, assert HEAD/tree/sole parent and **13 protected Git blob identities**, exact TWO MODIFY + ONE ADD path status, diff --check, clean.
- Python3.12 offline selected pytest ONLY these source safety surfaces: **tests/test_project_adoption_architecture_gate.py**, **tests/test_project_adoption.py**, **tests/test_architecture_governance.py**. Use -B, -q, -rA, -p no:cacheprovider, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and scoped project PYTHONPATH. Isolate process PG/DB/integration variables, redirect AppData via protected conftest, restore environment in finally. No actual DB/auth/provider/Claude startup.
- Print ALL individual PASSED/FAILED/ERROR test names and immediate PYTEST_EXIT_CODE, process env restoration, post HEAD/tree/13 exact blobs and both new/prior checkout clean, then VRES_168_A1_TEST_EXIT_CODE. Print **VRES_PERSONAL_168_A1_WINDOWS_SELECTED_TEST_COMPLETE** ONLY when exit0 and every postcheck passes. A STOP/ABORT must halt the one-block script; do not run follow-up fragments or claim success.
- Window test counts, exit status and final acceptance NOT_RUN at this handoff. Neither GitHub author source nor hypothetical model testing proves Python execution. Selected Windows test results cannot be transferred from parent Hook-R1 SHA.

## 4. Explicit unchanged holds / roadmap and next development cadence

**LIVE_SCHEMA_048_INCIDENT=OPEN:** absolutely NO PostgreSQL contact even SELECT, directly or via Vres CLI/MCP/task/bootstrap/doctor/health/hooks/F2/recovery. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** prior native Claude PT1 static review's four Read + three Grep automated Vres post-tool DB-route attempts were refused; source Hook-R1 corrected the exact Read/Glob/Grep PostToolUse matchers and user Windows tested 34 distinct PASS/exit0, but installed/global/managed/lifecycle hooks remain unverified and installed plugin is UNCHANGED. Therefore do NOT launch a new normal Claude Code review or install Hook-R1 solely based on source tests.

**Prior SHA-specific accepted evidence:** PT1 R1 selected Windows 189 PASS/exit0 plus independent STATIC_ACCEPT 0 blockers/five informationals, 7 refused host hook attempts. PT2A 213 PASS independent NOT_RUN; PT2B 43 PASS independent NOT_RUN; PT2C selected 54 PASS independent NOT_RUN; PT2D 50 PASS independent NOT_RUN. HOOK-R1 34 PASS independent NOT_RUN. This #168 A1 has not yet run selected tests or independent review. Preserve historical R0 failures and separate unattached alternate PT2C synthetic results. Last observed installed P2 Chairman Sonnet/high, requested Opus/medium UNINSTALLED, actual loaded family/effort UNKNOWN, strict F1 independently rooted positive authority BLOCKED. PERSONAL P0/P1/P2/P3 proportional policy, protected Fable/high router+validator and worker model/effort pins, current-user reusable secure credential handles, full V-01..V-42 functional backlog, Visual Studio fresh+legacy adoption, E7/PA/F2/go-live holds remain.

**The binding development cadence:** ChatGPT writes actual minimal code+tests on immutable SHA-pinned GitHub branch, operator executes one guarded Windows PowerShell block and supplies FULL console, ChatGPT evaluates/repairs real defects and records meaningful docs-only handoff; independent Claude Code with existing subscription evaluates only when a genuinely zero-automatic-DB-attempt environment is demonstrated, not by demanding API keys/account-type probes or Claude web Chat. Do not rerun green previous tests or turn the whole project into authorization ceremony. After this #168 source gate, progress a useful next component of full #168/#166/#167 offline development or safe E7/E8 learning work; actual protected installation stays separately authorized.
