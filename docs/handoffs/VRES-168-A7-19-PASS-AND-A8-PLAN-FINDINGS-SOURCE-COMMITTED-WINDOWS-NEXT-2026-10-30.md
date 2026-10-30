# Vres-OS PERSONAL #168 — A7 selected Windows 19 PASS; A8 plan-findings source committed; Windows A8 NEXT

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS.

**CURRENT:** A7_WINDOWS_SELECTED_19_DISTINCT_PASS_0_FAIL_0_SKIP_EXIT0 / A8_SOURCE_COMMITTED / A8_WINDOWS_TEST_NOT_RUN / A8_INDEPENDENT_CLAUDE_REVIEW_NOT_RUN / NO_INSTALLED_OR_REAL_PROJECT_CHANGE / LIVE_SCHEMA_048_AND_HOST_HOOK_INCIDENTS_OPEN.

## 1. Accepted A7 operator evidence

Read the [new A7 selected Windows acceptance handoff](VRES-168-A7-WINDOWS-19-PASS-EXIT0-AND-NEXT-BOUNDED-DEVELOPMENT-2026-10-30.md). User pasted the entire-looking PowerShell output with original P2 and A6 clean, verified official origin, fetched exact A7 SHA, fresh detached A7 exact HEAD/tree/parent and **21 protected Git blobs** before/after, exact 3-path allowlist, diff--check clean. ONE Python3.12 isolated `pytest -q -rA`: **13 new A7 and 6 inherited named tests PASSED, no FAIL/SKIP, PYTEST_EXIT_CODE=0**, disposable AppData unexpected refusals=0 / integration_opt_in=False, process DB/PG/integration vars restored, post-Git and both new/prior worktrees clean, `168_A7_TEST_EXIT_CODE=0`, `VRES_PERSONAL_168_A7_WINDOWS_SELECTED_TEST_COMPLETE`. Original chat paste, NOT raw Windows byte-attested log and NOT physical packet-level proof.

A7 source HEAD **65b2b41061f1c9f7815ff157570c73c9b5859668**, tree **34d2c29543091fa1e4ef06e6a77ace876d32745e**, accepted parent for A8. A7 read-only template/check for held legacy remains non-authorizing; KEEP/DROP and source audit constraints persist.

## 2. New bounded A8 — operator-facing architecture findings explanation (source committed, untested)

**Branch:** `feature/168-personal-offline-plan-findings-a8-20261030`.
**Published HEAD:** **f197ca9997b86bccb0fcb9bf6009dbc534d43391**.
**Tree:** **d282d7b6ad42470857e0b4f73a6f865478e1133c**.
**Sole parent:** accepted A7 **65b2b41061f1c9f7815ff157570c73c9b5859668**, tree 34d2c29543091fa1e4ef06e6a77ace876d32745e.
GitHub nonforce ref advance, exact HEAD/tree/sole parent and one-ahead/zero-behind compare verified.

**Exactly three files versus A7:**
1. M `src/vres_os/cli.py` Git blob **beaf4e6d12e14da706ae55dbb12348155184e68c**. Adds `vres project plan-findings --project <path>` for offline structured audit finding display; no project/plan writes, model or DB calls, and no activation.
2. M `src/vres_os/project_adoption.py` Git blob **b2da85d99ed196b8a31a9b03b803e6bbcef67bf4**. Adds `describe_alignment_findings()`, reuses the A7 shared read-only `_current_architecture_review` for existing/held legacy projects, reads material structural finding IDs only, returns sorted rule/title/recommendation/relative paths without raw source `evidence`; refuses more than 128 material rows or more than 65536 UTF-8 canonical JSON bytes; exports `activation_allowed=False`, `protected_validation_required=True`. Does not relax Fable/high or schema/Claude hold.
3. A `tests/test_project_adoption_plan_findings.py` Git blob **5a984d15e125ad2820addd1aad92b848ecf4be90**. Nine synthetic tests: deterministic material IDs match draft; no-Claude established held source; KEEP/DROP snapshot preservation; stale Claude and source refusal; missing state no-create; in-process CLI no DB/setup/models; >128 refuse without truncation; wrong root same key. None executed on user's Windows at this checkpoint. No full integration or independent code review is implied.

## 3. Next EXACT operator action — one atomic inline Windows selected test

Canonical complete PowerShell in `VRES-168-A8-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1` on this documentation branch. User MUST receive THE WHOLE script inline as ONE PowerShell code block, not fragments or a file-only prompt.

Requires original P2 `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` clean at 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c and accepted A7 `C:\Projects\Vres-ChatGPT-Review-168-Legacy-Plan-A7-20261030` clean at exact HEAD/tree. Fresh destination `C:\Projects\Vres-ChatGPT-Review-168-Plan-Findings-A8-20261030` MUST NOT exist.

One script checks remote/fetched exact A8 SHA, creates detached worktree, checks HEAD/tree/sole parent and **22 pinned Git blobs** before/after, exact M CLI / M adoption / A test allowlist, diff--check and both clean. Process-only DB/PG/integration scrub+finally restore; pytest plugin autoload off and Python -B. Selected only the nine new test functions via new module plus five exact relevant A7/A6/CLI compatibility test functions; expected selection size 14 **IF all collect normally**, no claimed PASS before run. Print all test names, immediate exit code, posttest 22 blobs + clean source/parent and final `VRES_PERSONAL_168_A8_WINDOWS_SELECTED_TEST_COMPLETE` only on exit0. STOP/ABORT => no fragmented retry; return full stdout/stderr.

## 4. Preserved hard limits and full product goals

`LIVE_SCHEMA_048_INCIDENT=OPEN` **NO PostgreSQL even SELECT**. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` seven historical automatic native Claude read/grep DB attempts, all refused; Hook-R1 source-only 34 Windows PASS does not prove installed/user/managed/lifecycle safe. Prior accidental Claude --safe-mode v2.1.312 / Opus 5.5 / Max session launched from PT2D directory after A7 path absent; it was NOT A7 independent review or Vres Chairman model installation, nor managed-hook clearance. Independent A8 Claude Code review held until no-hook safety confirmed.

No user profile change, install, credential copy, real project activation, issued Fable/high approval, model switch, database/health/bootstrap/F2, main merge, PR or release. Original P2 Chairman Sonnet/high last-observed, requested Opus/medium still uninstalled; physical effective policy separate from Claude interface label. Continue ChatGPT source+GitHub -> one SHA-pinned Windows selected offline gate -> reconcile -> minimal docs update -> independent Claude when safe -> next full-scope increment. Preserve entire V-01..V-42 register, PERSONAL P0-P3, PT1/2A–D, Hook-R1, #165–170, #174, E7/E8, current-user credentials, global Claude/PRISM and Data Source Registry, Visual Studio real legacy #169 and #170 go-live blockers. Do not infer a full release from one selected test.
