# Vres-OS — #165 F2 test-only Windows review worktree VERIFIED

Date: 2026-10-23, Europe/Athens.
Repository: vosser24/Vres-OS.
Source branch: feature/165-chairman-policy-foundation-20261023.
Documentation branch: docs/chatgpt-continuity-20261023.
Current disposition: **operator review worktree identity PASS; independent test-only Claude evaluation NOT_RUN.**
ChatGPT owns source/commits, Claude is independent evaluator only, user is Windows operator and consequential-action approver.

## 0. Exact currently checked-out source and immutable evidence

- **HEAD under review:** 36a41b6151b7520329ccc0ada0ff827d836ec579.
- **Immediate parent:** b77e0eef07976877e7f198a00484f5d13ce36889.
- Accepted parent F2 implementation: exact b77e0eef07976877e7f198a00484f5d13ce36889; Claude ACCEPT, 101/101 Windows offline PASS, exit 0. This acceptance remains bound to PARENT only, not to new tests.
- Diff from parent: exactly ONE path, tests/test_chairman_policy_history.py, modified; production module src/vres_os/chairman_policy_history.py was NOT changed and the new source commit has no CI status proof.
- GitHub source branch was re-read at exact full 40-character HEAD 36a41b6151b7520329ccc0ada0ff827d836ec579.
- **Prepared new isolated Windows review folder:** C:\Projects\Vres-ChatGPT-Review-165B1-F2-Tests-20261023.
- This documentation is an append-only checkpoint, not a runtime/installed model or PostgreSQL acceptance.

## 1. Windows operator returned verified success

User returned the output of the previously authorized full fail-stop PowerShell scriptblock:

    remote: Enumerating objects: 7, done.
    remote: Counting objects: 100% (7/7), done.
    remote: Compressing objects: 100% (4/4), done.
    remote: Total 4 (delta 3), reused 0 (delta 0), pack-reused 0 (from 0)
    Unpacking objects: 100% (4/4), 1.52 KiB | 91.00 KiB/s, done.
    From https://github.com/vosser24/Vres-OS
       b77e0ee..36a41b6  feature/165-chairman-policy-foundation-20261023 -> origin/feature/165-chairman-policy-foundation-20261023
    Preparing worktree (detached HEAD 36a41b6)
    HEAD is now at 36a41b6 test(chairman): isolate 129-entry and writer size-bound regressions

    === VERIFIED TEST-ONLY CHANGE ===
    tests/test_chairman_policy_history.py

    VRES_165_B1_F2_TESTS_REVIEW_READY
    REVIEW_PATH=C:\Projects\Vres-ChatGPT-Review-165B1-F2-Tests-20261023
    SHA=36a41b6151b7520329ccc0ada0ff827d836ec579

No STOP/fatal appears in the user-returned output. The script had preflight checks for 40-character full SHA, original P2 clean worktree HEAD, GitHub origin/remote SHA, fetched ref and exact immediate parent, new review directory absence, git worktree detached checkout, git diff --check, ONE changed-file allowlist and final worktree cleanliness before printing READY. This is an operator Git checkout PASS only; no independent test result has been produced for HEAD.

Do NOT re-fetch, recreate this directory, replace any earlier accepted worktree or run the previous full 101-case suite solely for this change.

## 2. Frozen R2 test-only change (not implementation)

The test-only commit addresses non-blocking reviewer findings on the already accepted b77e0eef:
- T1: version 128 is Sonnet/Medium; test now requests version 129 Opus/Medium, so count-bounded refusal is independently checked and not masked by no-op rejection. Expect match "bounded".
- T2: append a plausible serializable 129th proposal to a 128-entry canonical history; keep the document below 256KiB; require from_document to fail for "unbounded" proposal count, not document size.
- T3: rename the reader-size test honestly, and use a temporary monkeypatch of the module's size-limit constant to force the defensive to_document writer-bound failure; confirm reader-bound failure too. This monkeypatch is fixture-local and does not mutate installed config.
- T4: add whitespace between test functions.
No change to policy history implementation, activation, authority, code that accesses the database or installed Chairman settings.

The three specifically selected tests are:
1. test_full_128_entry_unicode_history_round_trips_under_same_byte_limit
2. test_reader_rejects_documents_over_declared_byte_limit
3. test_writer_refuses_canonical_output_over_its_effective_bound

## 3. Next authorized independent evaluation

Operator is currently in the prepared C:\Projects\Vres-ChatGPT-Review-165B1-F2-Tests-20261023 PowerShell directory.

Launch Claude Code from this review folder in the previously proven --safe-mode --permission-mode default mode with ONLY built-in Read/Glob/Grep/Bash and disallow mcp__*. Before launch in one fail-stop PowerShell scriptblock, re-verify HEAD == 36a41b6151b7520329ccc0ada0ff827d836ec579, HEAD^ == b77e0eef07976877e7f198a00484f5d13ce36889, clean status, only one test path in diff, and git diff --check. If safe-mode is rejected or Vres plugin/hooks start, STOP; do not fall back to an unsafe mode. Do not run start vres.

Claude is READ-ONLY independent evaluator: independently inspect the exact commit, source/test-only diff and preflight tests/conftest.py for isolated local temp app-data, protected root/fence, psycopg driver tripwires, PG/DB/GIT env cleanup, child process rejection and absence of credential use. If unsafe, return BLOCKED without executing tests. No additional Python probe, installation, fixture/source edit, login, MCP or external model runtime.

After safety preflight, authorize EXACTLY ONE selected offline test invocation from the current detached review directory:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_history.py -k "full_128_entry_unicode_history_round_trips_under_same_byte_limit or reader_rejects_documents_over_declared_byte_limit or writer_refuses_canonical_output_over_its_effective_bound"

Independently inspect whether 129th request is actually a different family and rejected for count, 129-entry input remains <=256 KiB and fails for count, and monkeypatch restores limit and exercises writer rather than only reader. Tests may deselect unrelated history tests; report actual collected, selected, passed, failed, error, skipped and deselected counts. Do not predeclare a PASS or claim an unrun count. Do not rerun unchanged Phase A, B1 or full F2 broad suites.

Claude returns a sanitized structured ACCEPT / REJECT / BLOCKED final verdict and exact SHA, parent, diff, exit code, counts and minimal defects. Any fix is ChatGPT's job only. A green test-only follow-up does not close #165 or resolve F1 independently authenticated history authority.

## 4. Unchanged higher-level evidence and safety holds

- Phase A R1 at 9c919271 independently REJECTED (39 passed, five failed, two errors); Phase A R2 at 11f2f8689308dfe43e482bca73aa57bb6467c788 independently accepted offline (53/53 PASS).
- B1 proposal-only source at f8237bb301dec160f33cab524727e6a0ec79b2c0 independently accepted offline (99/99 PASS).
- F2 256-KiB Unicode history implementation at b77e0eef07976877e7f198a00484f5d13ce36889 independently accepted offline (101/101 PASS).
- P2-A1 held-server contact guard R4 at 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 independently accepted offline (183/183 PASS), old R1/R2/R3 REJECT history preserved.
- Reviewer F1 remains OPEN: internally valid proposal history may be truncated/forked; a future adapter must obtain expected count/head/history hash from independently trusted user-event authority and protected validation. Hashes and free-text proposal rationales do not themselves confer permission.
- #165 is still OPEN/PARTIAL; Opus/medium is an in-memory candidate only. Shipped/installed Chairman Sonnet/high; no model switch or host physical evidence.
- Product main last verified 9a8acc5d464b96432a93cb95daa9581412fb07ee; original personal P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; installed release remains 20261022172833-4d82147b at last observation.
- LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL service last observed STOPPED; NO contact, including SELECT. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 open, positive trust issuance disabled, native trust not approved; PA-01..PA-08 incomplete. No real vault or secrets, install/upgrade, migrations, Vres startup/selftest, global Claude modification, signing or main merge without separate exact user approval.
- Full original V-01..V-42 backlog remains active for DEVELOPMENT only, not enabled runtime.

## 5. New-session resume prompt

RESUME Vres-OS from current HEAD of GitHub docs/chatgpt-continuity-20261023, read the current docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, THIS #165 F2 TEST-ONLY WINDOWS WORKTREE VERIFIED handoff, then the previous F2 ACCEPT/test-only handoff and B1/Phase A/P2-A1 accepted historical handoffs. The operator has ALREADY successfully created a new isolated Windows review directory C:\Projects\Vres-ChatGPT-Review-165B1-F2-Tests-20261023 at exact source commit 36a41b6151b7520329ccc0ada0ff827d836ec579 (parent accepted F2 b77e0eef07976877e7f198a00484f5d13ce36889), changed only tests/test_chairman_policy_history.py. Independent tests of this new test-only commit are NOT_RUN; do NOT repeat fetch/worktree-create or the old full 101-test suite. Next safely launch Claude evaluator and after conftest preflight run only the three selected boundary tests with -k, obtain exact status report. Keep #165 OPEN, F1 authenticated policy-history authority OPEN, installed Sonnet/high, schema-048 PostgreSQL incident held, credential/trust/PA controls unchanged. ChatGPT develops/commits, Claude independently evaluates, user operates Windows. After every substantive response update detailed docs handoff plus live index on docs/chatgpt-continuity-20261023 and report actual Git SHA.

## 6. Superseding F2 test-only independent ACCEPT (2026-10-23)

The operator supplied the complete independent Claude report on exact test-only SHA 36a41b6151b7520329ccc0ada0ff827d836ec579, parent accepted F2 b77e0eef07976877e7f198a00484f5d13ce36889. Final independent verdict ACCEPT limited to this test-only change; exactly three selected offline cases PASSED, exit code 0, zero failed/errors/skipped and no observed PostgreSQL/credential/worktree side effects. Pytest deselection count was not printed; reviewer approximation ~51 is INFERRED, not proof. Original source module remains unchanged, so prior F2 101/101 source acceptance is preserved. The preceding "NOT_RUN" text is now historical. See [the newest F2 test-only ACCEPT handoff](VRES-165-F2-TEST-ONLY-INDEPENDENT-ACCEPTANCE-2026-10-23.md). Remaining F1 external authenticated history prefix/fork authority is OPEN. Next is separate offline expected-history comparator work, with no activation.
