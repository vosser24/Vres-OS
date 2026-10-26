# Vres-OS #165 — PERSONAL C1 R1 Windows 29 individual PASS, independent OFFLINE evaluation pending

**Evidence date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Docs branch:** docs/chatgpt-continuity-20261023.
**Source branch:** feature/165-chairman-policy-foundation-20261023.
**CURRENT STATUS:** OPERATOR_C1_R1_OFFLINE_TEST_EXECUTION_PASS / 29 individual PASSED case IDs / PYTEST_EXIT_CODE=0 / protected AppData fence unexpected refusals=0 and integration_opt_in=False / post-test worktree clean / INDEPENDENT_CLAUDE_OFFLINE_EVALUATION_NOT_RUN / C1_R1_OFFLINE_ACCEPT_NOT_GRANTED / NOT INSTALLED.
**Evidence provenance:** FULL original uploaded 220-line Windows PowerShell console transcript embedded in section 7. Original uploaded file SHA-256 b98bd4f70801fa1ad78c18c7b7031b72d39029ffebb68298b659a7221505421b; 11,901 bytes. This is a hash of operator-provided file bytes, NOT a protected signature or OS-level attestation. GitHub may normalize text line endings; original console text itself is preserved.
**Operator-level review:** GitHub identities independently checked by ChatGPT; test execution is user-reported Windows stdout, not a Claude test or host observation.

## 0. Read first and precedence

Read CURRENT docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md then THIS C1 R1 Windows PASS evidence and:
1. docs/handoffs/VRES-165-PERSONAL-C1-R1-INDEPENDENT-STATIC-PASS-AND-ONE-OFFLINE-WINDOWS-TEST-GATE-2026-10-26.md — independent Claude STATIC_PASS with zero blocking findings on the NEW R1 short pytest-ID correction, Python selected test NOT_RUN at that historical point.
2. docs/handoffs/VRES-165-PERSONAL-C1-R1-PYTEST-ID-FIX-WINDOWS-CHECKOUT-READY-AND-STATIC-GATE-2026-10-26.md — guarded NEW C1 R1 detached Windows source worktree READY.
3. docs/handoffs/VRES-165-PERSONAL-C1-R1-WINDOWS-ENV-LIMIT-FAILURE-AND-BOUNDED-PYTEST-ID-SOURCE-2026-10-26.md — old C1 source Windows test EXIT1 (environment variable >32767), new distinct R1 one-line test-only correction.
4. docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — C0 pure preview already independently OFFLINE_ACCEPT at its own SHA, NOT an installed UI.
5. Historical A1 R2/A1 R1/B2A R3 and original Phase A/B1/F2/P2-A1 source and design per-SHA verdicts and full V-01..V-42 personal roadmap.

Do NOT rerun old failed C1 source; the new R1 source is a different SHA and already has one successful selected user Windows test. Do NOT claim R1 independent OFFLINE_ACCEPT until Claude independently evaluates this exact transcript.

## 1. Exact source identities and source-change scope

| Field | Exact SHA or path |
| --- | --- |
| **NEW C1 R1 feature commit / tested HEAD** | **7ac041018d4ec5a06be07318ecce5e140faccd91** |
| **NEW R1 source tree** | **0ef7af10335865231f4350e2dbb7ba561538ee00** |
| Direct parent, OLD C1 Windows test failure | **c545556a4ba9ba48f140e7379da960708a7f3c8d** |
| Exactly ONE MODIFIED path against parent | tests/test_chairman_selection_cli.py |
| **Corrected R1 test blob** | **e69b09cfca0878819096f8a6d211fbec0d7b3de1** |
| Old C1 parent test blob | **599dccb8dc10487796d71337f80a76f089024dbd** |
| UNCHANGED production CLI | src/vres_os/chairman_selection_cli.py blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1** |
| Independently accepted C0 pure preview | src/vres_os/chairman_selection_preview.py blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658** |
| Accepted Phase A policy | src/vres_os/chairman_policy.py blob **36e62d6a2712ac305fd4070bac658b94d61d155e** |
| Static Chairman plugin source | plugins/vres-os/agents/chairman.md blob **64cba93d6f69960350a0006b594734288f087ccc** |
| Protected test isolation | tests/conftest.py blob **1c33bb206dbf42691a6af9a709514bf3cc9994af** |
| Pytest config | pyproject.toml blob **b2d5e30d10d7be0613e90bf3ed1e346be5678969** |
| NEW tested detached review checkout | C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026 |
| OLD failed C1 checkout, retain historical | C:\Projects\Vres-ChatGPT-Review-165C1-CLI-20261026 |

ChatGPT separately read back GitHub feature HEAD/tree/parent and verified the one-modified-file source boundary. The operator guarded PowerShell preflight reports exact HEAD/tree/parent, all seven unchanged/new file blob IDs, historical old parent test blob, single M test path (not A), diff --check and clean detached worktree. Original installed Chairman and accepted C0 source are not modified by the R1 source revision.

## 2. Exact operator Windows offline test observations

**ONE selected executable call was echoed and run:**

    PYTEST_WORKTREE=C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026
    PYTHONPATH_SCOPED_TO_R1=C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026\src
    PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_cli.py

Evidence in the complete console:
- PRE-FLIGHT PASS was printed with exact R1 source SHA before Python.
- Pytest progressed to 100%, followed by a PASSES section. **29 individual lines** start with PASSED tests/test_chairman_selection_cli.py::. No separately printed 29 passed / collected footer or elapsed time is present. The 29 is a COUNT of visible PASSED case IDs; do not invent a summary footer, collection total or duration.
- Crucial repaired case passed as an individually reported test: PASSED tests/test_chairman_selection_cli.py::test_invalid_source_bytes_are_refused_without_rendering[oversized-template].
- Other cases cover user-friendly preview without apply, exactly one fixed repo-relative read, LF and CRLF, no-op, model-only and effort-only, version display and bad versions, invalid model/effort choices, absent source root or template, five malformed/invalid template inputs, mismatch baseline, no guessed source location, and no positive DB/installer/provider surface.
- No FAIL, ERROR, SKIP, xfail/xpass, or pytest warnings section appears in the observed output.
- LIVE APP-DATA FENCE reports unexpected refusals=0, protected current-user Local and Roaming VresOS paths, trusted disposable %TEMP% session, expected init order, removed_env=['GIT_ASKPASS'], integration_opt_in=False. These are in-process isolation/driver-stub observations, NOT full OS/network/physical PostgreSQL no-contact attestation.
- The PowerShell wrapper printed **PYTEST_EXIT_CODE=0** immediately after the single subprocess invocation. The exit code is wrapper-reported process status, not a status line printed by pytest.
- Scoped PYTHONPATH was restored in finally and THEN verified by the script against its saved original value; PYTHONPATH_RESTORED printed with no STOP. The earlier failed C1 snippet had only an unconditional label; this R1 script visibly checked equality.
- Post-run R1 HEAD and tree PASS, plus POST_RUN_WORKTREE_CLEAN (tracked/untracked porcelain). Final C1_R1_TEST_EXECUTION_PASS_PENDING_INDEPENDENT_EVALUATION and VRES_165_C1_R1_OFFLINE_TEST_COMPLETE markers appeared.
- No split standalone PowerShell ELSE exception appeared during this new R1 test.
- The tests create disposable pytest-owned tmp_path fixture files. They do not prove runtime source-checkout preview was manually invoked or installed; they exercise the CLI main() against disposable sources.

**Scope:** operator-execution PASS at NEW R1 SHA; independent report-only acceptance is PENDING. No separate full pytest 29-collected footer was printed, no runtime installed-model attestation.

## 3. Earlier independent STATIC_PASS is NOT the offline verdict

Prior independent Claude R1 STATIC_PASS has zero blocking issues, final marker VRES_165_C1_R1_PYTEST_ID_FIX_STATIC_REVIEW_COMPLETE and status PYTEST_NOT_RUN at review time. Its full reads were the corrected R1 test (1–216) and C1 CLI (1–115); pyproject, conftest and accepted C0/Phase A only partly examined by Grep. It confirmed that explicit pytest.param id="oversized-template" yields a short ID and retains original 524,289-byte fixture and negative assertions. The original failed old C1 traceback was incomplete; new R1 oversized-template PASSED is actual positive outcome evidence that the environmental limit no longer blocks that case on this invocation, but cannot reconstruct the old exact stack.

Old C1 c545556a4ba9ba48f140e7379da960708a7f3c8d remains static PASS but selected Windows test EXIT1, NOT independent offline acceptance.

## 4. NEXT: ONE independent Claude REPORT-ONLY evidence evaluation, no tools

The operator should use an existing NEW C1 R1 Claude session if available, otherwise start ONE fresh Claude Code session in the NEW R1 review folder. Do NOT use old failed C1/A1 sessions. Pass the exact FULL 220-line transcript reproduced in section 7.

No Git/Bash/PowerShell, Python/pytest, CLI, Read/Grep, MCP, Vres task/DB, provider/model, agent/subagent or source editing is needed for the evidence-only verdict. Claude should:
1. State SHA/tree and blob identities are operator/GitHub-relayed, NOT Git measured by Claude.
2. Independently count all 29 printed PASSED IDs, including repaired oversized-template, distinguish the missing pytest collected/footer/duration, and check that only one new R1 test invocation is present.
3. Check exact R1 worktree/CWD and temporary R1/src Python path, exit0, in-process AppData fence refusals0/integration opt-in false, scripted PYTHONPATH restoration check and HEAD/tree/worktree clean. Do not assert OS-level or native network/DB certification.
4. Preserve old C1 Windows exit1 at OLD SHA, earlier R1 STATIC_PASS, and the new short-ID stress case result. Do not invent old traceback details.
5. Return exactly one verdict **OFFLINE_ACCEPT / OFFLINE_REJECT / EVIDENCE_BLOCKED** for the PERSONAL source-checkout READ-ONLY C1 R1 source/test boundary at NEW exact SHA. No positive user consent, installed model switch, installer or shipped user workflow granted.
6. Declare **NO_TEST_RERUN / NO_SOURCE_MODIFICATION / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION / NO_POSTGRESQL_CONTACT_BY_REVIEWER**, and finish marker **VRES_165_C1_R1_INDEPENDENT_OFFLINE_EVALUATION_COMPLETE**.
7. Stop after report. ChatGPT will separately seal the final accept/reject in docs only when the independent report actually returns.

## 5. PERSONAL incident and installed-model constraints

LIVE_SCHEMA_048_INCIDENT=OPEN means ABSOLUTELY NO PostgreSQL contact, even SELECT. Protected conftest in-process psycopg tripwire and app-data fence do not grant PostgreSQL permission. Do not Vres task/DB probe or bootstrap despite VRES_PERSISTENCE_WARNING and VRES_REPLY_GUARD_WARNING. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..08 unfinished.

Installed Chairman is last operator-reported Sonnet/high; proposed Opus/medium UNINSTALLED. C1 source-checkout command is NOT an installed vres command or actual active host observation. Original F1/#165 authenticated user permission, independent protected history/validator remains OPEN. No credentials/vault/keyring, global Claude hooks/settings/plugins, Fable/provider model call, signing, installer, installed model change, physical #169 host proof, PR/main merge or release from offline preview source acceptance.

Historical independent pure C0 OFFLINE_ACCEPT at e6bd8cb8f92a779da1469efe738709918e9da6df: 34 individual PASS/exit0 with later C0-PROC-01 PowerShell ELSE nonblocking. A1 R2 9754b190083a0ada757ebee07f2ef5b8f312b58e: 93 PASS/exit0; A1 R1 1b406c788057f0cb2a8a57578b89110a11b76161: 71 PASS/exit0; B2A R3 32847410952e9d4620bf7046cbee4a41a7ddc73b: 95 PASS/exit0 and R3-PROC-01. Earlier B2A R2 91/92 REJECT and initial static REJECT, B2B v0/R1/R2 DESIGN_REVISE, R3 DESIGN_ACCEPT strictly DENY-ONLY, older Phase A/B1/F2/P2-A1 per-SHA verdicts and V-01..V-42 roadmap all retained.

## 6. Docs-only seal and next-session resume

This new 220-line evidence handoff and one modified docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md are the ONLY two expected documentation paths on the canonical docs branch, starting at verified previous docs HEAD **7c3859013751c9eea7aed45497c0045f1b7a4717**, tree **699ceb2ededad2083865607a009a55e71fd0b8cf**. Verify recursive two-path doc delta, no deletes, source HEAD unchanged; create one-parent docs commit, nonforce expected-old ref update, read back docs and source and blobs. No feature/source change or test invocation here.

**NEW SESSION RESUME:** C1 R1 feature SHA **7ac041018d4ec5a06be07318ecce5e140faccd91**, tree **0ef7af10335865231f4350e2dbb7ba561538ee00**, direct OLD FAILED C1 parent **c545556a4ba9ba48f140e7379da960708a7f3c8d**, one modified corrected C1 test blob **e69b09cfca0878819096f8a6d211fbec0d7b3de1**, prior test blob **599dccb8dc10487796d71337f80a76f089024dbd**, unchanged standalone C1 CLI blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1** and previous C0/Phase A/template/conftest/pyproject unchanged. NEW R1 Windows detached checkout C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026 is clean. Independent Claude R1 STATIC_PASS zero blockers, then user ONE selected Windows R1 pytest **29 individually PASSED cases incl oversized-template, exit0, AppData fence unexpected refusals0/integration opt-in false, R1 cwd/PYTHONPATH scoped and restored, post HEAD/tree/porcelain clean**. No 29-collected/footer/time printed. R1 **INDEPENDENT OFFLINE_ACCEPT PENDING**; next Claude report-only full user transcript evaluation, no rerun or source edits. Do not transfer test PASS to old failed C1 SHA. Original F1/#165 OPEN, installed Sonnet/high unchanged, Opus/medium UNINSTALLED, LIVE_SCHEMA_048 NO PostgreSQL even SELECT, earlier protected credential/provider/global Claude/installer/main holds and unresolved Vres persistence warnings. Preserve all original per-SHA verdicts and V-01..V-42 personal roadmap.


```text
PS C:\Users\User> 
PS C:\Users\User> $ErrorActionPreference = "Stop"
PS C:\Users\User> 
PS C:\Users\User> $review = "C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026"
PS C:\Users\User> 
PS C:\Users\User> $head = "7ac041018d4ec5a06be07318ecce5e140faccd91"
PS C:\Users\User> $tree = "0ef7af10335865231f4350e2dbb7ba561538ee00"
PS C:\Users\User> $parent = "c545556a4ba9ba48f140e7379da960708a7f3c8d"
PS C:\Users\User> 
PS C:\Users\User> function Assert-Exact {
>>     param(
>>         [string]$Label,
>>         [string]$Actual,
>>         [string]$Expected
>>     )
>> 
>>     if ($LASTEXITCODE -ne 0 -or $Actual.Trim() -cne $Expected) {
>>         throw "STOP: $Label mismatch"
>>     }
>> 
>>     Write-Host "PASS: $Label"
>> }
PS C:\Users\User> 
PS C:\Users\User> Write-Host "=== C1 R1 OFFLINE TEST PREFLIGHT ==="
=== C1 R1 OFFLINE TEST PREFLIGHT ===
PS C:\Users\User> 
PS C:\Users\User> if (-not (Test-Path -LiteralPath $review -PathType Container)) {
>>     throw "STOP: Corrected R1 review folder missing"
>> }
PS C:\Users\User> 
PS C:\Users\User> $actual = git -C $review rev-parse HEAD
PS C:\Users\User> Assert-Exact "R1 HEAD" $actual $head
PASS: R1 HEAD
PS C:\Users\User> 
PS C:\Users\User> $actual = git -C $review rev-parse 'HEAD^{tree}'
PS C:\Users\User> Assert-Exact "R1 tree" $actual $tree
PASS: R1 tree
PS C:\Users\User> 
PS C:\Users\User> $actual = git -C $review rev-parse 'HEAD^'
PS C:\Users\User> Assert-Exact "Old C1 parent" $actual $parent
PASS: Old C1 parent
PS C:\Users\User> 
PS C:\Users\User> $checks = @(
>>     @("Corrected R1 tests", "tests/test_chairman_selection_cli.py", "e69b09cfca0878819096f8a6d211fbec0d7b3de1"),
>>     @("Unchanged C1 CLI", "src/vres_os/chairman_selection_cli.py", "6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1"),
>>     @("Accepted C0", "src/vres_os/chairman_selection_preview.py", "1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658"),
>>     @("Phase A policy", "src/vres_os/chairman_policy.py", "36e62d6a2712ac305fd4070bac658b94d61d155e"),
>>     @("Chairman template", "plugins/vres-os/agents/chairman.md", "64cba93d6f69960350a0006b594734288f087ccc"),
>>     @("Protected conftest", "tests/conftest.py", "1c33bb206dbf42691a6af9a709514bf3cc9994af"),
>>     @("Pytest config", "pyproject.toml", "b2d5e30d10d7be0613e90bf3ed1e346be5678969")
>> )
PS C:\Users\User> 
PS C:\Users\User> foreach ($check in $checks) {
>>     $actual = git -C $review rev-parse "HEAD:$($check[1])"
>>     Assert-Exact $check[0] $actual $check[2]
>> }
PASS: Corrected R1 tests
PASS: Unchanged C1 CLI
PASS: Accepted C0
PASS: Phase A policy
PASS: Chairman template
PASS: Protected conftest
PASS: Pytest config
PS C:\Users\User> 
PS C:\Users\User> $actual = git -C $review rev-parse 'HEAD^:tests/test_chairman_selection_cli.py'
PS C:\Users\User> Assert-Exact "Old C1 test blob" $actual "599dccb8dc10487796d71337f80a76f089024dbd"
PASS: Old C1 test blob
PS C:\Users\User> 
PS C:\Users\User> $branch = @(git -C $review branch --show-current)
PS C:\Users\User> 
PS C:\Users\User> if ($LASTEXITCODE -ne 0 -or $branch.Count -ne 0) {
>>     throw "STOP: R1 checkout is not detached"
>> }
PS C:\Users\User> 
PS C:\Users\User> $changed = @(git -C $review diff --name-status --no-renames $parent $head)
PS C:\Users\User> 
PS C:\Users\User> if ($LASTEXITCODE -ne 0) {
>>     throw "STOP: R1 source diff failed"
>> }
PS C:\Users\User> 
PS C:\Users\User> $expected = "M`ttests/test_chairman_selection_cli.py"
PS C:\Users\User> 
PS C:\Users\User> if (($changed -join "`n") -cne $expected) {
>>     throw "STOP: Unexpected changed-file scope"
>> }
PS C:\Users\User> 
PS C:\Users\User> git -C $review diff --check $parent $head --
PS C:\Users\User> 
PS C:\Users\User> if ($LASTEXITCODE -ne 0) {
>>     throw "STOP: Diff integrity failed"
>> }
PS C:\Users\User> 
PS C:\Users\User> $before = @(git -C $review status --porcelain=v1 --untracked-files=all)
PS C:\Users\User> 
PS C:\Users\User> if ($LASTEXITCODE -ne 0 -or $before.Count -ne 0) {
>>     throw "STOP: R1 review worktree dirty before test"
>> }
PS C:\Users\User> 
PS C:\Users\User> Write-Host "PREFLIGHT_PASS"
PREFLIGHT_PASS
PS C:\Users\User> Write-Host "R1_SOURCE_SHA=$head"
R1_SOURCE_SHA=7ac041018d4ec5a06be07318ecce5e140faccd91
PS C:\Users\User> 
PS C:\Users\User> Write-Host "=== ONE SELECTED C1 R1 OFFLINE PYTEST ==="
=== ONE SELECTED C1 R1 OFFLINE PYTEST ===
PS C:\Users\User> 
PS C:\Users\User> $previousPythonPath = [Environment]::GetEnvironmentVariable(
>>     "PYTHONPATH", "Process"
>> )
PS C:\Users\User> 
PS C:\Users\User> $testExit = $null
PS C:\Users\User> 
PS C:\Users\User> Push-Location -LiteralPath $review
PS C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026> 
PS C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026> try {
>>     $env:PYTHONPATH = Join-Path -Path $review -ChildPath "src"
>> 
>>     Write-Host "PYTEST_WORKTREE=$((Get-Location).Path)"
>>     Write-Host "PYTHONPATH_SCOPED_TO_R1=$env:PYTHONPATH"
>>     Write-Host "PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_cli.py"
>> 
>>     & py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_cli.py
>>     $testExit = $LASTEXITCODE
>> }
>> finally {
>>     [Environment]::SetEnvironmentVariable(
>>         "PYTHONPATH",
>>         $previousPythonPath,
>>         "Process"
>>     )
>> 
>>     Pop-Location
>> }
PYTEST_WORKTREE=C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026
PYTHONPATH_SCOPED_TO_R1=C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026\src
PYTEST_COMMAND=py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_selection_cli.py
.............................                                                                                                          [100%]
================================================================== PASSES ===================================================================
LIVE APP-DATA FENCE: unexpected refusals=0 protected=['c:\\users\\user\\appdata\\local\\vresos', 'c:\\users\\user\\appdata\\roaming\\vresos'] trusted_temp_base=C:\Users\User\AppData\Local\Temp session_root=C:\Users\User\AppData\Local\Temp\vres-pytest-app-data-jfiifyf5\VresOS init_order=['validate-temp-base', 'create-session-directory', 'validate-session-directory', 'create-app-data-root', 'enable-isolation'] removed_env=['GIT_ASKPASS'] integration_opt_in=False
========================================================== short test summary info ==========================================================
PASSED tests/test_chairman_selection_cli.py::test_user_command_prints_ascii_only_preview_no_apply_and_no_changes
PASSED tests/test_chairman_selection_cli.py::test_single_fixed_repository_relative_file_is_read_once
PASSED tests/test_chairman_selection_cli.py::test_both_native_newline_styles_preview_without_writing[lf]
PASSED tests/test_chairman_selection_cli.py::test_both_native_newline_styles_preview_without_writing[crlf]
PASSED tests/test_chairman_selection_cli.py::test_identical_model_effort_has_explicit_noop_display
PASSED tests/test_chairman_selection_cli.py::test_model_only_and_effort_only_are_distinct[opus-high-Model: sonnet -> opus-Effort: high -> medium]
PASSED tests/test_chairman_selection_cli.py::test_model_only_and_effort_only_are_distinct[sonnet-medium-Effort: high -> medium-Model: sonnet -> opus]
PASSED tests/test_chairman_selection_cli.py::test_explicit_policy_versions_are_display_only
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[0]
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[-1]
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[1000001]
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[auto]
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[1.5]
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[01]
PASSED tests/test_chairman_selection_cli.py::test_invalid_version_is_argparse_error_before_any_template_read[+1]
PASSED tests/test_chairman_selection_cli.py::test_invalid_model_or_effort_never_falls_back[--reported-model-fable]
PASSED tests/test_chairman_selection_cli.py::test_invalid_model_or_effort_never_falls_back[--reported-effort-auto]
PASSED tests/test_chairman_selection_cli.py::test_invalid_model_or_effort_never_falls_back[--proposed-model-auto]
PASSED tests/test_chairman_selection_cli.py::test_invalid_model_or_effort_never_falls_back[--proposed-effort-extreme]
PASSED tests/test_chairman_selection_cli.py::test_missing_explicit_source_root_is_refused_before_disk_read
PASSED tests/test_chairman_selection_cli.py::test_missing_source_template_is_neutral_and_does_not_echo_root
PASSED tests/test_chairman_selection_cli.py::test_invalid_source_bytes_are_refused_without_rendering[]
PASSED tests/test_chairman_selection_cli.py::test_invalid_source_bytes_are_refused_without_rendering[not valid frontmatter]
PASSED tests/test_chairman_selection_cli.py::test_invalid_source_bytes_are_refused_without_rendering[---\nname: validator\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\n]
PASSED tests/test_chairman_selection_cli.py::test_invalid_source_bytes_are_refused_without_rendering[\xff]
PASSED tests/test_chairman_selection_cli.py::test_invalid_source_bytes_are_refused_without_rendering[oversized-template]
PASSED tests/test_chairman_selection_cli.py::test_baseline_disagreement_is_refused_not_a_live_model_check
PASSED tests/test_chairman_selection_cli.py::test_missing_requested_template_subpath_is_not_scanned_or_guessed
PASSED tests/test_chairman_selection_cli.py::test_module_has_no_db_installer_or_provider_integration_surface
PS C:\Users\User> 
PS C:\Users\User> $restoredPythonPath = [Environment]::GetEnvironmentVariable(
>>     "PYTHONPATH", "Process"
>> )
PS C:\Users\User> 
PS C:\Users\User> if ($restoredPythonPath -cne $previousPythonPath) {
>>     throw "STOP: PYTHONPATH restoration verification failed"
>> }
PS C:\Users\User> 
PS C:\Users\User> Write-Host "PYTHONPATH_RESTORED"
PYTHONPATH_RESTORED
PS C:\Users\User> 
PS C:\Users\User> if ($null -eq $testExit) {
>>     throw "STOP: Pytest exit code not captured"
>> }
PS C:\Users\User> 
PS C:\Users\User> Write-Host "PYTEST_EXIT_CODE=$testExit"
PYTEST_EXIT_CODE=0
PS C:\Users\User> 
PS C:\Users\User> Write-Host "=== C1 R1 POST-TEST INTEGRITY ==="
=== C1 R1 POST-TEST INTEGRITY ===
PS C:\Users\User> 
PS C:\Users\User> $actual = git -C $review rev-parse HEAD
PS C:\Users\User> Assert-Exact "Post-test R1 HEAD" $actual $head
PASS: Post-test R1 HEAD
PS C:\Users\User> 
PS C:\Users\User> $actual = git -C $review rev-parse 'HEAD^{tree}'
PS C:\Users\User> Assert-Exact "Post-test R1 tree" $actual $tree
PASS: Post-test R1 tree
PS C:\Users\User> 
PS C:\Users\User> $after = @(git -C $review status --porcelain=v1 --untracked-files=all)
PS C:\Users\User> 
PS C:\Users\User> if ($LASTEXITCODE -ne 0 -or $after.Count -ne 0) {
>>     throw "STOP: R1 worktree changed during test"
>> }
PS C:\Users\User> 
PS C:\Users\User> Write-Host "POST_RUN_WORKTREE_CLEAN"
POST_RUN_WORKTREE_CLEAN
PS C:\Users\User> 
PS C:\Users\User> if ($testExit -eq 0) {
>>     Write-Host "C1_R1_TEST_EXECUTION_PASS_PENDING_INDEPENDENT_EVALUATION"
>> }
C1_R1_TEST_EXECUTION_PASS_PENDING_INDEPENDENT_EVALUATION
PS C:\Users\User> 
PS C:\Users\User> if ($testExit -ne 0) {
>>     Write-Host "C1_R1_TEST_EXECUTION_NONZERO_PRESERVE_EVIDENCE"
>> }
PS C:\Users\User> 
PS C:\Users\User> Write-Host "VRES_165_C1_R1_OFFLINE_TEST_COMPLETE"
VRES_165_C1_R1_OFFLINE_TEST_COMPLETE
PS C:\Users\User> 
```
