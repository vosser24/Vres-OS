# Vres-OS PERSONAL — HOOK-R1 read-only PostToolUse source correction committed; one guarded Windows test NEXT

Date: 2026-10-29 Europe/Athens. Repo: vosser24/Vres-OS.
**CURRENT:** PERSONAL_HOOK_R1_SOURCE_COMMITTED / SOURCE_STATIC_MATCHER_DRAFT_VERIFIED / WINDOWS_HOOK_R1_SELECTED_PYTEST_NOT_RUN / INDEPENDENT_CLAUDE_REVIEW_NOT_RUN / INSTALLED_PLUGIN_UNCHANGED / DB_INCIDENT_OPEN / NO_USER_ACTION_YET.

## 0. Original full-scope methodology remains binding

Follow the independent [ChatGPT-Led Full-Scope Delivery Plan](../roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md), [original 2026-10-22 lead-scope checkpoint](VRES-CHATGPT-LEAD-SCOPE-REACTIVATION-CHECKPOINT-2026-10-22.md), [full V-01..V-42 functionality register](../roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md), then the [newest canonical continuity index](VRES-CHATGPT-CONTINUITY-INDEX.md). ChatGPT authors source, tests and GitHub commits, user runs exact guarded Windows steps, Claude Code with existing subscription independently consumes and reviews the exact clean pinned checkout when safe. No new subscription/API-key setup, account probes, web Chat substitution, global configuration changes, or endless ceremony. Focus on delivering real features. Preserve separate immutable source/testing/review/installed-state evidence.

## 1. Exact immutable source commit

Source feature branch: **feature/personal-hook-readonly-posttool-fence-20261029**.
Published HEAD **891fb22287b6ee8b028eda7256c0b5639df40c04**.
Published tree **1b9d7ddcc4f6c8e0cafda8cea5e1c5d51e3ca9db**.
Sole parent PT2D Windows-selected source HEAD **a5913288b7748693adafc36c9c1cb35af3ea3949**, tree **d45ffc91781be6681124ff369af5df4d06300ce9**.
GitHub compare parent..HEAD: exactly **ONE commit ahead, ZERO behind, TWO changed paths**:
- MODIFY plugins/vres-os/hooks/hooks.json old Git blob **5833973d9be6ccf4263dda2d461cc5994d30416c**, NEW Git blob **e286e4be47d058ee6ed6a3169fc45803aedc0df1**, 3 matcher lines updated (+3/-3).
- ADD tests/test_hook_readonly_posttool_fence.py, NEW Git blob **97c2bb75ae31ff98a5ce66c450d4f51d6e12f15a**, 141 source lines, 10 focused parametrized test functions.

Source update published through NONFORCED expected-old GitHub ref CAS and independently verified exact branch HEAD/tree/sole parent/file blob readback. No installer, release_artifact.py, install_recovery.py, current-user/global Claude configuration, native host hooks, original Chairman, any PostgreSQL code, secrets or product main changed.

## 2. Specific proven incident cause and limited fix

At PT1 R1 independent Claude Code source review, four built-in Read and three built-in Grep calls caused seven AUTOMATIC PostToolUse plugin MCP "reply_activity_observe" database-route ATTEMPTS. The Vres database contact guard REFUSED all seven, so no successful SQL is evidenced, but the no-attempt condition failed. Original pinned plugin hooks.json additionally registered broad PostToolUse experience observer invoking the installed runtime CLI, also sensitive to unexpected side effects.

New Git SOURCE hook matchers now exclude ONLY the exact built-in names Read, Glob and Grep from:
1. PostToolUse command vres-experience-observe.ps1;
2. PostToolUse MCP reply_activity_observe;
3. PostToolUseFailure MCP reply_activity_observe.

The old PreToolUse read-tool exclusion was already present and remains unchanged. Exact action-tool names Bash, Write, Edit and the explicit experience_retrieve MCP tool remain eligible for observer hooks; the dedicated work-unit and AskUserQuestion hooks remain, historical recursion exclusions and SubagentHandback experience skip remain, and no other event's hook registration changes.

The new test module checks that every PostToolUse and PostToolUseFailure registration yields ZERO matching groups for each Read/Glob/Grep; preserves existing PreToolUse read exclusion, action tool routing, recursion exceptions, work-unit hook, AskUserQuestion special hook, SubagentHandback exemption, exact-only non-prefix behavior, and unchanged lifecycle event presence. Source-side JSON parse and JS regex draft preflight for selected canonical names passed before commit; **this is NOT Windows pytest acceptance**.

**Critical NONCLAIM:** This amendment does NOT automatically change the installed Vres plugin or current session, and does not eliminate session-start, prompt-submission, stop/compact, installed/global/managed or unknown Claude lifecycle hooks. It does NOT certify a no-PostgreSQL-attempt native Claude Code review. Do not start/restart native Claude Code or install/update the current-user/global plugin under this checkpoint. A later safe scoped review method is still required. This is a **bounded direct root-cause fix** for exactly the seven ordinary read-tool posthook attempts, not an all-hooks bypass.

## 3. Operator's one next Windows action, exact script

Archived guarded Windows validation script:
docs/handoffs/VRES-PERSONAL-HOOK-R1-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-29.ps1, blob **b8f859c7affc635bb4bae4239028a7a90f71e855**, 171 LF lines. It derives conservatively from the already executed 166-line PT2D SHA-pinned guarded Windows script and independently checks the expected unique path and pre/post anchors. Paste the COMPLETE one-atomic-block script INLINE in ChatGPT, not just a file/link.

It guards:
- Original source anchor **C:\Projects\Vres-P2F-Postinstall-Hardening-20261022**, expected P2 HEAD **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, must be clean.
- Prior PT2D selected review source **C:\Projects\Vres-ChatGPT-Review-Personal-PT2D-20261029**, expected parent HEAD **a5913288b7748693adafc36c9c1cb35af3ea3949** and tree **d45ffc91781be6681124ff369af5df4d06300ce9**, must be clean.
- NEW detached **C:\Projects\Vres-ChatGPT-Review-Personal-HOOK-R1-20261029**, must NOT already exist.
- Official origin URL and remote expected HOOK-R1 head; fetch exact published branch, new detached worktree; HEAD/tree/sole parent, **20 protected Git blobs** (new hook JSON/test plus inherited PT2A/B/C/D, Chairman, pytest conftest, installer/recovery and three historical hook regression test files), exactly ONE M hook JSON plus ONE A test, diff --check and clean.
- ONLY selected Python3.12 offline tests, no Claude: tests/test_hook_readonly_posttool_fence.py (new), tests/test_plugin_contract.py (existing), tests/test_e6_reference_hooks.py::test_matcher_is_broadened_but_excludes_subagent_handback_and_keeps_the_launcher, tests/test_e6_observability_hook.py::test_hooks_json_registers_one_successful_posttooluse_observer.
- py -3.12 -B -m pytest -q -rA -p no:cacheprovider with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, guarded disposable AppData/psycopg conftest, process-only DB/PG/integration environment clear and finally restoration, no installed plugins or files touched.
- Print all selected named PASS/FAIL, PYTEST_EXIT_CODE, POSTTEST exact HEAD/tree/20 blobs and both clean statuses, HOOK_R1_TEST_EXIT_CODE. Only on exit0 and all postchecks print **VRES_PERSONAL_HOOK_R1_WINDOWS_SELECTED_TEST_COMPLETE**. If ANY STOP/ABORT, do not run individual remainder commands; paste entire console output instead.

Do not preclaim a test count/Windows pass. Neither new source nor user Windows hook tests have been reviewed by Claude and nothing installed. Post-operator: independently count every named test and exit/fence/restore/pre/post Git identity; seal a new docs-only Windows PASS/FAIL checkpoint while preserving all prior history.

## 4. Legacy status and future delivery

Historic exact selected Windows source tests: PT1 R1 189 PASS/exit0 + independent STATIC_ACCEPT 0 blockers/5 informationals (PT1 Claude review included 7 refused automatic hook attempts), PT2A 213 PASS/exit0 independent NOT_RUN, PT2B 43 PASS/exit0 independent NOT_RUN, PT2C 54 PASS/exit0 independent NOT_RUN, PT2D 50 PASS/exit0 independent NOT_RUN. PT2C alternate unattached SHA 59d811... remains distinct, never Windows accepted. The new hook R1 feature is a new SHA and needs its own test and independent static review. Source-only candidate is not installation.

**LIVE_SCHEMA_048_INCIDENT=OPEN: ABSOLUTELY NO PostgreSQL even SELECT**, direct or indirect via Vres MCP/tasks/CLI/doctor/bootstrap/hooks/F2. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN** (seven DB route attempts refused). VRES_REPLY_GUARD_WARNING and VRES_PERSISTENCE_WARNING remain unresolved; no probes. Original installed P2 Chairman last observed Sonnet/high, requested Opus/medium UNINSTALLED, physical loaded model UNKNOWN; no real release-v2 pointer/source provenance backup/rollback verification, user install consent or F1 positive authority. PERSONAL P0/P1/P2/P3, protected Fable/high validator/router and worker pins, current-user secure reusable credentials, Visual Studio new/legacy project onboarding, V-01..V-42, E7/PA/F2/go-live holds unchanged.

**NEXT after this isolated hook test:** resolve any real test defect on a new feature SHA; if selected source/test PASS, plan a proportionate safe Claude Code source-only review with lifecycle/no-DB constraints, while continuing independent unblocked PERSONAL functional delivery instead of spinning further model switch planning contracts. No automatic installation or extra preflight/account checks.
