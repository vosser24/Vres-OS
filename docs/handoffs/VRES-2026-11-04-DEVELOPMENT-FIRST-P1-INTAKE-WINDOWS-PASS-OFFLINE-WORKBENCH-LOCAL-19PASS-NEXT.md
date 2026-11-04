# Vres-OS — 2026-11-04 DEVELOPMENT FIRST: project intake Windows PASS; offline workbench 19 local PASS; Windows workbench NEXT

**Checkpoint 2026-11-04, Europe/Athens.** PERSONAL daily operations for ONE Windows user, not enterprise IAM or multitenancy. The owner explicitly prioritized meaningful development with one relevant test per new feature. This record is continuity, not a release or installed pilot. All absolute incident holds still apply.

## Canonical GitHub identities (readback verified this session, before this docs commit)

Repository https://github.com/vosser24/Vres-OS
Documentation branch docs/chatgpt-continuity-20261023 BEFORE this checkpoint: HEAD 1c40d4979ec70cf8da561f3303b798d643d38d6f, TREE a4f7bcfc29fc89058a3143cd9f17145a9a059588, SOLE parent 292f28f4c13d4eed9152d84fa9f118439cb14530. Verify NEW docs commit HEAD/TREE/parent after publication; do not self-attest future refs. READ FIRST docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md. Previous handoff docs/handoffs/VRES-2026-11-04-P1-SANDBOX-R2-PREPARED-FIRST-LAUNCH-HELD-CHECKPOINT.md and linked P3 incidents handoff remain canonical historical evidence.

Product main unchanged: 9a8acc5d464b96432a93cb95daa9581412fb07ee / TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7. NO main merge.

Accepted Bundle B: HEAD 00ff9e1a03a652cfcb1fdcbd7a09e53bfc3af788, TREE 6816f280fd388f1921bcff235da97a68be87ede5.
Previously accepted P1 source env fence feature/personal-p1-offline-release-no-launch-env-fence-20261104: HEAD 23908842246ab148ba645386486426f210917980, TREE c6b7d2c661573862d75239783637901764d99a50, SOLE Bundle B parent 00ff9e1a03a652cfcb1fdcbd7a09e53bfc3af788.

**Project-intake feature** feature/personal-p1-readonly-project-intake-20261104: HEAD c01b5cb8fa5c0aa25b6eccbe53abe4d32b114203, TREE c0f4990a06b1a55f055f9e9495d8503f82081374, sole parent 3ac2edcec18b9697e169724abc4fb09d016753cc. Since P1 env fence exactly two added source/test files: src/vres_os/personal_project_intake.py blob 63fa8bb35bef68940195b8e4b463bfebaf7b2a13; tests/test_personal_project_intake.py blob 5ce024b6723c876dba8da1204b0349be97ae15d9. Source statically accommodates the existing #168 scanner's unknown risk for sensitive/unreadable files.

**NEW latest development** feature/personal-p1-offline-workbench-20261104: HEAD 3e6bf1c0a6fa85d453f51fbd51ef6f945206513d, TREE 1b1934ec36a4ae9694832351f2c17592e5a52582, sole parent c01b5cb8fa5c0aa25b6eccbe53abe4d32b114203. Exactly TWO added paths over intake: src/vres_os/personal_offline_workbench.py blob 636d40b7229d27da6442e8089120cad0c3840529; tests/test_personal_offline_workbench.py blob 6b31de8be32ce20c3c3ecdeca93be6f26c9ba803. These blobs MATCH exact locally executed Python 3.13.5 test source bytes. All publishes used dedicated feature branches, non-force expected-parent SHA; no product main or installed changes.

Historical installed P2 source HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, TREE 205c081277ece483c634e1c801c39595abd4549c. No current physical installed-release bytes, pointer, hooks or user profile independently read: do not infer live installed state.

## Operator-pasted P1 Windows real scanner test (ACCEPT WITH PROVENANCE LIMIT)

The owner pasted these exact success lines after running the selected P1 project-intake test in ordinary PowerShell 5.1:

PASS: EXACT_GITHUB_SOURCE
PASS: OFFLINE_PYTHON_3_13_17
PASS: REAL_SCANNER_FRESH_PROJECT
PASS: REAL_SCANNER_LEGACY_HOOK_REVIEW
PASS: NO_PROJECT_WRITES_OR_HOST_CHILD_EXECUTION
P1_INTAKE_WINDOWS_INTEGRATION=PASS
INTEGRATION_EXIT_CODE=0
GATE_EXIT_CODE=0
DISPOSABLE_TEST_ROOT=C:\Projects\Vres-Intake-Test-c25b07da522a

Scope: exact source checkout and tree, actual existing #168 scanner on TWO disposable projects, internal socket/subprocess monkeypatch assertions, no intended real project edits. The quoted NO_HOST_CHILD line is a Python assertion from the test script, NOT independent OS-level no-contact observation. No original native transcript/stdout/stderr uploaded. This is a focused real-scanner integration, NOT full pytest or installed-system acceptance.

Immediately afterward, the operator entered PowerShell FINALLY as a standalone command after the prior completed gate. PowerShell returned a CommandNotFoundException for finally. This is a separate shell syntax/invocation error, not a failure of the selected Vres integration test. Environment-restoration code in that standalone FINALLY was NOT_RUN; exact saved process-environment restore/compare was NOT verified. ChatGPT instructed the owner to CLOSE the original PowerShell process and open a fresh normal window: process-scoped environment edits then end, but its closure was not independently observed. Do NOT needlessly rerun the intake integration solely for this shell error.

Disposition: **P1_INTAKE_WINDOWS_REAL_SCANNER_SELECTED_PASS_WITH_OPERATOR_PASTED_PROVENANCE_AND_ENV_RESTORE_NOT_VERIFIED**.

## NEW workbench software milestone: what actually works in source

New stdlib module personal_offline_workbench.py provides ONE useful manually authored Markdown scratch document instead of another fixed synthetic demo. preview_note produces metadata and SHA without writes or content echo. create_note requires caller approval, an ABSENT absolute ordinary workspace with basename Vres-Workbench-*, a caller-selected TASK-* label, and Markdown text. It creates ONLY a new scratch workspace, notes/next-step.md, and draft-receipt.json, never overwrites existing paths; it verifies exact digest readback. inspect_note verifies exact file layout, no redirect/hardlink, bounded bytes and receipt integrity. undo_note requires explicit approval and exact note SHA, refuses changed note/stale receipt/extra files, and removes only owned unchanged scratch note/receipt and now-empty workspace. Standalone source-file CLI supports create, inspect, undo via explicit absolute user-owned note file and scratch directory, --yes for creation and undo, and hides exception details/paths in CLI errors.

The task label and receipt are NOT an authoritative Vres persistent task store, approval, validated artifact or independent Fable verdict; no installer, native Claude, PostgreSQL, credential, model call, real project adoption or installed profile access. This is the practical beginning of V-41 useful bounded document outputs and V-42 low ceremony, not an installed daily-use claim. User content should not include real credentials because the scratch Markdown itself is plaintext; receipts do not contain note text.

**Actual tests:** Local disposable ChatGPT container Python 3.13.5, pytest 9.0.2; first author-only test run **10 PASSED / 7 FAILED** due an exact-Path type check rejecting PosixPath, corrected before any GitHub feature source commit. Corrected first suite **17 PASSED / 0 FAILED**; after adding standalone CLI integration cases **19 PASSED / 0 FAILED**, one selected pytest invocation with PYTHONPATH=src and PYTHONDONTWRITEBYTECODE=1, runtime ~0.11s; py_compile PASS. Tested exact author files matched GitHub source/test blob SHAs above. Windows native workbench test **NOT_RUN**. Full parent-repository/regression suites **NOT_RUN** on the new source. Installed Vres and real daily pilot **NOT_RUN**. Do not attribute intake Windows PASS to this newer workbench commit.

## Holds, provenance and deferred Sandbox: unchanged

LIVE_SCHEMA_048_INCIDENT=OPEN — historical F2 child escape migrated LIVE PostgreSQL control 041 to 048. NO PostgreSQL EVEN SELECT, direct or indirect; no database migration/recovery/health/CLI/MCP.
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN — seven old installed Claude posttool DB route attempts were refused; no trusted full installed lifecycle acceptance. NO ordinary native Claude Code or installed hooks.
Independent trusted F1/Fable positive approval NOT GRANTED. No source/self-reported validator can grant it.
P2 installation consent NOT_REQUESTED/NOT_AUTHORIZED. No install.ps1/update.ps1, credentials/PRISM/current-user config, installed P2 overwrite, real legacy project or main merge. No real daily-use pilot.

Previously prepared Windows Sandbox R2 remains NOT_LAUNCHED. Windows 11 24H2+ first-launch Microsoft Store host client-update possibility NOT separately authorized; do not start default Sandbox or prepared .wsb. Original R4 pinned checkout and R2 Python 3.13.17 NuGet/52 wheels were reported with exact provenance limitations in earlier handoff; 216 paths are Git inventory NOT a staged manifest; exact P1 source artifact stage, guest pytest and real 216-file release manifest NOT_RUN. The new intake/workbench code can be developed and tested without launching Sandbox: defer it.

Preserve original V-01..V-42, personal M0–M8, issues #165–#170/#174/#176, #163/#164, E7/F2/C2B/R0, Stage1–6, all original rejected attempts, current protected worktrees and the separate 22/187/41/144/125/254 prior selected Windows source-scoped PASS provenance. Previous accepted test results are never silently transferred to a new commit.

## ONE exact next development/test operation

**Run exactly one focused native Windows PowerShell 5.1 offline workbench test on pinned GitHub feature HEAD 3e6bf1c0a6fa85d453f51fbd51ef6f945206513d, TREE 1b1934ec36a4ae9694832351f2c17592e5a52582**, outside Claude. Use a fresh normal PowerShell process, an entirely NEW C:\Projects disposable checkout and scratch input, and existing previously acquired Python 3.13.17 NuGet package after relevant scoped byte check. Do not invoke pip, Sandbox, installed Vres, real legacy, PostgreSQL or native Claude. Run standalone source-file CLI create -> inspect -> undo against a fresh NEW Vres-Workbench-* folder and a user-safe synthetic Markdown input file; confirm digest, receipt and exact input preservation, output directory removed, source HEAD/TREE correct, and tests/exit codes. If setting process environment variables, restore inside ONE fully syntactically closed block with actual readback; never paste FINALLY as a separate command. Prefer avoid env edits entirely. No previously accepted 22/187/41/144/125/254 reruns and no new giant gate. Record exact PASS/FAIL/NOT_RUN and source SHA.

Once Windows workbench test is accepted, proceed to the next meaningful user-selected project/task/document workflow and source integration; do not invent another standalone task database, enterprise IAM or endless synthetic cases. Do not mutate a real project until explicitly scoped user permission.

## Hard checkpoint

This documentation checkpoint is made conservatively early given unavailable precise context-window use. Publish only this handoff plus canonical READ FIRST index on docs branch, non-force expected-old-SHA lease, verify remote HEAD/TREE/sole parent and content. End this ChatGPT session after full inline fresh-chat prompt and recommend starting a new chat. No async handoff or local Windows file commit claims.
