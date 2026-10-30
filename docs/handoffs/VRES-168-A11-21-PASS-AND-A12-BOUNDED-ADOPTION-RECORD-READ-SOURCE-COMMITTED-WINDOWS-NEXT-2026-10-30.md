# Vres-OS PERSONAL #168 — A11 Windows 21 PASS / exit0; A12 bounded non-follow adoption record read SOURCE COMMITTED, Windows A12 NEXT

**Date:** 2026-10-30 Europe/Athens. **Repo:** vosser24/Vres-OS.

**CURRENT:** A11_WINDOWS_SELECTED_ACCEPTED_21_PASS_0_FAIL_0_SKIP_EXIT0 / A12_SOURCE_COMMITTED / A12_WINDOWS_NOT_RUN / A12_INDEPENDENT_CLAUDE_REVIEW_NOT_RUN / NO_INSTALLED_VRES_OR_REAL_PROJECT_CHANGE / LIVE_SCHEMA_048_AND_CLAUDE_POSTTOOL_DB_ROUTE_INCIDENTS_OPEN.

## 1. A11 tested acceptance and parent identity

See [A11 Windows acceptance handoff](VRES-168-A11-WINDOWS-21-PASS-EXIT0-ACCEPTANCE-2026-10-30.md). A11 feature `feature/168-personal-decision-record-integrity-a11-20261030` HEAD **d58db1b5cea0c74040f1d25a219e80e0180c8efd**, tree **ffd65c706e1a42c04a3c687918925082eb19d607**, direct A10 Windows accepted parent `8304a7e17afbcc521c941cb7cb76c3d380951768`. User's complete-looking PowerShell console shows original P2 and prior A10 exact clean, official GitHub origin, remote/fetched A11 SHA, new detached A11 exact SHA/tree/parent, **26 protected blobs before and after**, two-file M adoption/A tests allowlist, diff--check clean, 15 new and six inherited **21 individually named PASSED**, zero fail/skip, `PYTEST_EXIT_CODE=0`, `168_A11_TEST_EXIT_CODE=0`, temporary AppData unexpected refusals0/integration_opt_in False, process PG/DB/integration env restored, both A11 and A10 worktrees clean and final `VRES_PERSONAL_168_A11_WINDOWS_SELECTED_TEST_COMPLETE`. Operator chat-pasted log, NOT independently captured raw CRLF SHA or physical packet/SQL attestation. A11 independent Claude NOT_RUN, installed Vres/main unmodified.

## 2. A12 SOURCE COMMITTED — bounded adoption JSON record-read fence, Windows tests NOT_RUN

**Branch:** `feature/168-personal-adoption-record-read-fence-a12-20261030`.

**Published A12 source HEAD:** **345a568b551ac23183c54f10611335adee903b96**.

**Git tree:** **0851934f4a79e297e136d512f6ae6d1e6f707e2d**.

**Sole parent:** Windows-accepted A11 **d58db1b5cea0c74040f1d25a219e80e0180c8efd**, tree `ffd65c706e1a42c04a3c687918925082eb19d607`. Exact GitHub branch CAS, HEAD/tree/parent and one-ahead/zero-behind compare verified.

**Exactly TWO paths changed:**
1. M `src/vres_os/project_adoption.py`, Git blob **3fa8d0c5721b8125c44eead127f6a3cb9b85e9eb**. Change only private `_read_json` record readback and add `_MAX_ADOPTION_RECORD_BYTES=2*1024*1024`. A missing file still returns None without creating state. An existing record must be regular and nonlinked, its immediate parent must be ordinary nonlinked, and the recorded size may not exceed 2 MiB. Use `O_NOFOLLOW` for file opens where available and compare `lstat` vs opened `fstat` identity, size and modification time before reading, then compare again after a bounded read. Bad UTF-8, malformed or excessively nested JSON, vanishing/raced, linked, special or oversized files refuse with sanitized recovery-required message; no file contents are echoed. Does not add a positive consent issuer, unconditionally approve an adoption, modify installed hooks or attempt any DB access. The identity checks and immediate-parent test are additional defenses, **not a proof against all ancestor swaps or a cryptographic signature**.
2. A `tests/test_project_adoption_record_read_fence.py`, Git blob **6b38396e2710d267108233476399eb3ca852e6e5**, **12 authored synthetic regression functions**: legitimate deterministic JSON, missing no-create, simulated Windows reparse-point file and parent junction rejection, synthetic special-file refusal, >2MiB refusal, open identity race, vanished between lstat/open, invalid UTF-8, malformed JSON, excessive nesting, permission-error redaction. No real user records/credentials/native Claude/models/PostgreSQL.

**A12 Windows tests NOT_RUN, independent Claude Code source review NOT_RUN.** A12 source commit and static GitHub identity do not claim tests PASS.

## 3. One next operator action

[Complete A12 SHA-pinned atomic Windows selected-test script](VRES-168-A12-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1) is archived in docs at Git blob **16d7aa97784846ae4fa356552420089c75bcfca8**. Provide script to operator **entirely INLINE in ONE PowerShell code block**, not fragments/file-only.

The original P2 `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` must be clean at `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`. Previously tested accepted A11 `C:\Projects\Vres-ChatGPT-Review-168-Decision-Integrity-A11-20261030` must be clean at A11 SHA/tree. Fresh destination `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030` **MUST NOT EXIST**. Official remote, fetched exact A12 SHA, new detached worktree exact HEAD/tree/sole parent, **27 protected pinned blobs pre/post**, exact M adoption source + A new test module, diff--check, new and prior clean.

One Python 3.12 `-B -m pytest -q -rA -p no:cacheprovider` selection of 12 new A12 tests and seven exact accepted A11/P2-D/A7 compatibility functions (**19 planned if all collect; NOT preclaimed PASS**). Process-only PG/DB/integration vars isolated and restored in finally, pytest plugin autoload disabled, disposable protected AppData fixture, immediate actual test exit, posttest HEAD/tree/27 blob and checkout cleanliness. Successful finish only with no failed/unexpected skipped cases, `PYTEST_EXIT_CODE=0`, `168_A12_TEST_EXIT_CODE=0`, `VRES_PERSONAL_168_A12_WINDOWS_SELECTED_TEST_COMPLETE`. On STOP/ABORT do not run fragments or modify checkout; report entire stdout/stderr and preserve failed evidence.

## 4. Non-negotiable safety holds and roadmap

**LIVE_SCHEMA_048_INCIDENT=OPEN:** NO PostgreSQL even SELECT via direct driver, Vres task/MCP/CLI/bootstrap/hooks/migration/doctor/recovery/F2. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** seven earlier native Claude Code Read/Grep post-tool automatic DB-route attempts, all refused. Hook-R1 source 34 Windows selected PASS did NOT prove installed/global/managed/lifecycle hook clearance. Prior accidental Claude Code `--safe-mode` session from PT2D displayed Claude Code v2.1.312/Opus 5.5 Max, but did not constitute any A7–A12 independent source review, installed Vres Chairman model change or server-managed no-hook clearance. Original installed P2 Chairman Sonnet/high last observed; requested Vres Opus/medium uninstalled. Positive independently rooted F1 authority blocked, protected Fable/high not approved. No real project, user config/credentials, Vres installed package, model, network, database, product main, PR/merge or go-live operation.

Continue small, observable ChatGPT-led source development using exact accepted SHA parent -> new dedicated GitHub feature branch + tests -> one entire SHA-pinned offline Windows PowerShell selected gate -> full console reconciliation -> minimal docs-only seal -> independent Claude only after hook safety clearance. Retain PERSONAL P0-P3, PT1/2A–D/Hook-R1, #168 A1–A11 full accepted/rejected/skip evidence, all V-01..V-42, #165–170, #174, #176 E7/E8, global Claude/PRISM adoption #166, current-user Data Source Registry #167, Visual Studio real legacy #169 and go-live #170.
