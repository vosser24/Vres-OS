# Vres-OS PERSONAL #168 — A13 Windows 28 PASS / 1 FAIL / exit1 REJECTED; A13 R1 preserves A12 parent diagnostics, Windows NEXT

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS. **Source of evidence:** user-supplied generated large-paste text attachment (167 lines / about 11 KB, mounted in this ChatGPT turn). It reproduces their ordinary Windows PowerShell output. It is NOT an independently SHA-256-attested raw Windows stdout file or a physical network/SQL/managed-hook attestation.

**CURRENT:** A12_R1_WINDOWS_SELECTED_ACCEPTED_23PASS_EXIT0 / A13_ORIGINAL_WINDOWS_REJECTED_28PASS_1FAIL_EXIT1 / A13_R1_SOURCE_COMMITTED_WINDOWS_NOT_RUN / INDEPENDENT_CLAUDE_SOURCE_REVIEW_NOT_RUN / LIVE_SCHEMA_048_AND_NATIVE_CLAUDE_HOOK_INCIDENTS_OPEN / NO_INSTALLED_OR_REAL_PROJECT_OPERATION.

## 1. Original A13 exact source and Windows rejection

Feature `feature/168-personal-adoption-ancestor-link-fence-a13-20261030`, **ORIGINAL REJECTED A13 HEAD cdaa39aaa774cef88a4831bf6b157e380fbb69d9**, tree **59979714d813c6b72a885b33dff13da62bdeef8c**, sole accepted A12 R1 parent **80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966**, tree `259e507b79dd7a2034ba9c9350f943665df13fbe`. The original A13 changed two paths relative to A12 R1: M `src/vres_os/project_adoption.py` blob **0360d845bf0124c04d89039241acc1ee1bec993d**, A `tests/test_project_adoption_record_ancestors.py` blob **d9689edcc8a68160e44767b9bf918f1da12eebb6**.

Operator ran the exact archived A13 complete atomic PowerShell `VRES-168-A13-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1` (Git blob `1ab2cfec08fd0c288be1d882884963ca9cc1561a`). Preflight explicitly reported PASS original P2 anchor `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` HEAD `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c` clean; prior accepted A12 R1 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-R1-20261030` exact SHA/tree clean; original rejected A12 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030` rejected SHA/tree clean. Official GitHub origin, remote+fetched A13 SHA, new detached A13 `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-20261030` at exact SHA/tree/commit ancestry, **28 protected Git blobs before and after**, M/A allowlist, diff--check and checkout clean PASS; `VRES_PERSONAL_168_A13_PREFLIGHT_PASS`.

**TEST DISPOSITION: REJECTED.** Python 3.12 `-B -m pytest -q -rA -p no:cacheprovider` selected nine new A13 + sixteen previously accepted A12 R1 record-read functions + four older safety/compatibility cases, **28 individually named PASSED, one FAILED**; the single failure was `tests/test_project_adoption_record_read_fence.py::test_parent_junction_is_refused_before_record_open`. The A12 test expected regex `not a bounded ordinary file`, but A13 emitted `Adoption record state.json has an unsafe ancestor directory; recovery is required`. **The simulated unsafe immediate-parent junction WAS refused before file open; the incompatibility is the established diagnostic string, not a newly permitted read.** `PYTEST_EXIT_CODE=1`, `168_A13_TEST_EXIT_CODE=1`, and correct `VRES_PERSONAL_168_A13_ABORTED: STOP: A13 selected pytest exited with code 1`, no success marker.

The original Windows test also reported temporary protected AppData fence unexpected refusals0 and integration_opt_in=False, process DB/PG/integration env isolated and restored (`PROCESS_ENVIRONMENT_RESTORED`), and exact A13 HEAD/tree/28 pinned blobs posttest PASS, clean A13, accepted A12 R1 and original rejected A12 worktrees. Keep these facts, and preserve this **original A13 28PASS/1FAIL/exit1** rejection permanently. Do not replace failed evidence by R1 acceptance.

## 2. A13 R1 narrow source correction on the SAME branch

**A13 R1 corrected HEAD:** **007a51b05d6c0e3d43086a864558fb666853d58d**.
**Tree:** **1bc85ebbbe2ac4e62dc96aa89c896395b239aef3**.
**Sole parent:** original rejected A13 `cdaa39aaa774cef88a4831bf6b157e380fbb69d9`. GitHub published nonforce expected-parent update and independent compare shows exactly one commit ahead / zero behind and two MODIFIED paths (no unrelated files).

- M `src/vres_os/project_adoption.py` Git blob **887c0f4e006ee3cac4e14534e38fcf83840deb1c**. In `_record_ancestor_identity`, a linked/non-directory *immediate parent* retains the previously accepted A12 generic sanitized error `not a bounded ordinary file; recovery is required`. Unsafe **higher ancestors** retain the new A13 `unsafe ancestor directory` message. Both cases still refuse without opening leaf. All existing 2MiB, no-follow, descriptor identity, JSON 128-depth and ancestor before/after checks retained. This preserves a pre-existing diagnostic rather than editing an accepted A12 test to hide a changed contract.
- M `tests/test_project_adoption_record_ancestors.py` Git blob **eb8a67704d0c38030ff7d700d2b52ae8d8afb138**. Preserve all nine original A13 tests; add three synthetic immediate-parent compatibility tests: link denied before leaf, immediate parent non-directory old diagnostic, immediate-parent changed-to-link after reading old refusal; total **12 authored A13 R1 tests**. All 16 unchanged A12 R1 record-read regression tests stay in scope.

**A13 R1 SOURCE COMMITTED, WINDOWS NOT_RUN; independent Claude Code security review NOT_RUN.** No new commit should be called accepted before operator's exact Windows evidence.

## 3. EXACT next operator action — one complete atomic A13 R1 Windows test

Canonical SHA-pinned complete script: [`VRES-168-A13-R1-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1`](VRES-168-A13-R1-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1), verified Git blob **cc1d950d082b23dd11c7d7d573243320755f8531**. The operator requires **ONE FULL INLINE PowerShell CODE BLOCK**, no fragments/file-only commands. Preflight checks:
- Original P2 clean exact SHA `82c82430...`.
- Accepted A12 R1 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-R1-20261030`, exact `80cee6...`/tree, clean.
- Original rejected A12 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030`, exact rejected SHA/tree clean.
- Original rejected A13 `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-20261030`, exact rejected `cdaa39...`/tree clean.
- FRESH detached R1 destination `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-R1-20261030` MUST NOT EXIST.
- Official remote, fetched exact corrected A13 R1 SHA, detached HEAD/tree and complete A13/A12/A11 ancestry; **28 pinned protected source/test/hook/installer blobs pre/post**; exactly two MODIFIED files versus original rejected A13, `git diff --check`, clean new/rejected/accepted worktrees.
- One guarded Python3.12 `pytest -q -rA` process-only DB/PG/integration isolation and restoration, plugin autoload off. **12 A13 R1 functions +16 A12 R1 record-read +four earlier regression functions =32 planned; no preclaimed PASS**. Success: `PYTEST_EXIT_CODE=0`, `168_A13_R1_TEST_EXIT_CODE=0`, zero failed/unexpected skipped and final `VRES_PERSONAL_168_A13_R1_WINDOWS_SELECTED_TEST_COMPLETE`. On STOP/ABORT preserve full console and all worktrees, no fragmented retry.

## 4. Unlifted safety and full program

**LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT**, direct or Vres CLI/MCP/bootstrap/doctor/migrations/hooks/recovery/F2. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** seven historical native Claude Code Read/Grep posttool automatic DB routes refused; Hook-R1 34 selected Windows PASS source-only does not clear installed/global/managed/lifecycle hooks. Prior accidental Claude Code `--safe-mode` UI from PT2D did not independently review A13 or clear installed hooks; provider UI Opus 5.5 Max not installed P2 Chairman Opus/medium policy. Original P2 Chairman Sonnet/high last seen. Positive F1 rooted issuance and protected Fable/high validator not approved. No real legacy project, credentials, user/global config, installed Vres, model policy, live DB, main merge/PR, deployment or release action.

Maintain all accepted/rejected/skip checkpoints PT1/PT2A-D, Hook-R1, #168 A1–A12 R1, original A13 rejection, PERSONAL P0–P3, full V-01..V-42, #165–170, #174, #176 E7/E8, global Claude/PRISM #166, Data Source Registry and current-user credentials #167, Visual Studio real project #169 and go-live #170. Cadence: ChatGPT commits narrow source/tests -> ONE atomic SHA-pinned offline Windows PowerShell run -> user entire console -> explicit acceptance or exact correction -> docs seal. Independent native Claude review only after no-hook boundary separately proven safe.
