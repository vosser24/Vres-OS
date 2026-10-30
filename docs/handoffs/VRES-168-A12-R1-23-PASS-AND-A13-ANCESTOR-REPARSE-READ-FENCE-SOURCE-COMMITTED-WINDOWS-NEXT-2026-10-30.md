# Vres-OS PERSONAL #168 — A12 R1 guarded Windows 23 PASS/exit0; A13 ancestor record-link fence source committed, Windows A13 NEXT

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS.
**Current state:** A12_R1_WINDOWS_SELECTED_ACCEPTED_23PASS_0FAIL_0SKIP_EXIT0 / ORIGINAL_A12_REJECTED_18PASS_1FAIL_EXIT1 / A13_SOURCE_COMMITTED / A13_WINDOWS_NOT_RUN / A13_INDEPENDENT_CLAUDE_NOT_RUN / NO_REAL_PROJECT_OR_INSTALLED_ACTION / LIVE_SCHEMA_048_AND_CLAUDE_AUTO_HOOK_INCIDENTS_OPEN.

## A12 R1 selected acceptance and historical rejection

Read [the exact A12 R1 23-PASS acceptance](VRES-168-A12-R1-WINDOWS-23-PASS-EXIT0-ACCEPTANCE-2026-10-30.md). Corrected feature `feature/168-personal-adoption-record-read-fence-a12-20261030` HEAD **80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966**, tree **259e507b79dd7a2034ba9c9350f943665df13fbe**; its direct intermediate parent `6730da195ba3d4e4bb62841e7c03ee11ec0e004a` descended from **ORIGINAL REJECTED** `345a568b551ac23183c54f10611335adee903b96` (original Windows 18 pass, one deep-JSON failure, exit1). Original rejected Windows checkout `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030` and earlier accepted A11 clean. R1 source record depth cap 128 with quoted/escaped delimiters.

The operator executed the guarded R1 script in a fresh detached `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-R1-20261030`. Exact R1 HEAD/tree/full ancestry, original P2, accepted A11 and rejected A12 clean, **27 protected Git blobs before and after**, two modified file net allowlist and diff--check PASS; 16 R1 record-read tests plus 7 inherited = **23 individually named PASSED, 0 FAIL/SKIP, PYTEST_EXIT_CODE=0, 168_A12_R1_TEST_EXIT_CODE=0**, temporary AppData fence unexpected refusals0, integration_opt_in False, process DB/PG/integration env finally restored; posttest all 27 blobs and checkout cleanliness PASS, `VRES_PERSONAL_168_A12_R1_WINDOWS_SELECTED_TEST_COMPLETE`. Evidence is user-pasted console, not byte-level original Windows log attestation, full suite, physical SQL network proof or independent Claude review.

## NEW #168 A13 — all-ancestor saved adoption JSON reparse/race preview defense (SOURCE COMMITTED; Windows NOT_RUN)

**Feature branch:** `feature/168-personal-adoption-ancestor-link-fence-a13-20261030`.
**Published A13 HEAD:** **cdaa39aaa774cef88a4831bf6b157e380fbb69d9**.
**Tree:** **59979714d813c6b72a885b33dff13da62bdeef8c**.
**Sole parent:** previously Windows accepted A12 R1 **80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966**. GitHub branch was created at this parent and advanced nonforce with exact expected-SHA ref; HEAD/tree/parent and one-ahead/zero-behind two-file compare verified.

**Exactly TWO source-changed paths from accepted A12 R1:**
- M `src/vres_os/project_adoption.py` Git blob **0360d845bf0124c04d89039241acc1ee1bec993d**. Add `_record_ancestor_identity(path)`, scanning every existing ancestor directory **root-first** via `_lstat` before touching persisted record metadata, refusing symlink/junction/reparse and non-directory components. Preserve missing record/missing path returns `None` without creating state. After bounded record read, recheck all ancestors' metadata identities and refuse altered/disappeared parents before parsing JSON. The A12 R1 2MiB, no-follow where supported, file fstat before/after and deterministic JSON depth gates are unchanged. **This is a best-effort pathname consistency check; not atomic directory-descriptor traversal or proof against every ancestor TOCTOU attack.**
- A `tests/test_project_adoption_record_ancestors.py` Git blob **d9689edcc8a68160e44767b9bf918f1da12eebb6**; 9 authored synthetic tests: valid deep ordinary state read repeat/no-write, missing ancestors no-create, linked grandparent denial before leaf metadata, non-directory higher ancestor denial, inode swap after record read, disappearing ancestor after read, newly linked ancestor postread, exactly two scans and sanitized errors. No real profile, credential, native Claude hooks or PostgreSQL.

**A13 Windows tests NOT_RUN, independent Claude Code security review NOT_RUN.** Do not pre-accept source or test cases.

## Next exactly ONE operator action — full atomic A13 Windows selected test

Canonical archived [A13 guarded PowerShell script](VRES-168-A13-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1), Git blob **1ab2cfec08fd0c288be1d882884963ca9cc1561a**. User requires the **entire script inline, in ONE self-contained PowerShell code block** without fragments or file-only prompt.

Original P2 anchor `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` must be clean at `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`. Previously selected-accepted corrected R1 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-R1-20261030` must be clean at exact R1 HEAD/tree. Original REJECTED A12 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030` must be preserved clean at rejected SHA/tree. NEW detached destination `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-20261030` MUST NOT exist.

Official GitHub origin, remote/fetched exact A13 SHA; fresh detached HEAD/tree, immediate R1 parent and full R1 intermediate -> rejected A12 -> accepted A11 chain; **28 protected Git blobs pre/post**; exact M `project_adoption.py` / A new test module; diff--check and worktree cleanliness. One process-only Python3.12 `-B -m pytest -q -rA -p no:cacheprovider` selected **9 new A13 + 16 previously accepted A12 R1 record-read tests + 4 relevant A11/P2-D/A7 compatibility = 29 planned tests, none claimed PASS before execution**. Pytest plugin autoload disabled, process PG/DB/integration env isolated and finally restored, disposable AppData test fence, immediate exit code and posttest 28 SHA/clean checks.

Success requires no failed/unexpected skip, `PYTEST_EXIT_CODE=0`, `168_A13_TEST_EXIT_CODE=0`, `VRES_PERSONAL_168_A13_WINDOWS_SELECTED_TEST_COMPLETE`. On any STOP/ABORT: no fragment reruns, do not touch original rejected A12/R1 worktrees, send complete console for narrowly corrected source and immutable rejected evidence.

## Non-negotiable incident holds / full roadmap

`LIVE_SCHEMA_048_INCIDENT=OPEN`: absolutely **NO PostgreSQL even SELECT**, including Vres CLI/MCP/hooks/bootstrap/migrations/doctor/F2/recovery. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: seven historical native Claude Code tool-Read/Grep auto-posttool DB attempts refused. Hook-R1 source 34 offline selected PASS did NOT clear installed/global/managed/lifecycle hooks. Accidentally opened prior Claude `--safe-mode` UI from PT2D was not an independent A12/A13 review, managed-hook clearance, or Vres Chairman Opus/medium installed model switch; original installed Chairman Sonnet/high last observed. Positive F1 independent authority and protected Fable/high still blocked. No real legacy project, installed Vres, profile/global Claude, native credentials, PostgreSQL, PR/merge, main branch or release action permitted.

Carry forward full V-01..V-42, PERSONAL P0-P3, PT1/PT2A-D/Hook-R1 and #168 A1-A12 accepted/rejected/skip evidence, #165–170, #174, #176 E7/E8, #166 global Claude/PRISM, #167 current-user Data Source Registry, Visual Studio real legacy #169 and go-live #170. Keep ChatGPT-led small exact-GitHub-parent source+tests -> one complete SHA-pinned offline PowerShell selected Windows gate -> user whole console -> accept/reject -> docs seal -> independent Claude only after hook-safety evidence.
