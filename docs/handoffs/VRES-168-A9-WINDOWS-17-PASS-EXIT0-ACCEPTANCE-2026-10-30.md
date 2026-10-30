# Vres-OS PERSONAL #168 A9 — Windows selected 17 PASS / exit 0 acceptance

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS. **Source evidence:** operator pasted the complete-looking ordinary Windows PowerShell output in this ChatGPT project conversation; no raw CRLF stdout file, byte-level SHA-256 attestation, or packet-level network capture was supplied.

## 1. Exact Windows acceptance

**A9_WINDOWS_SELECTED_ACCEPTED:** 17 distinct explicitly named `PASSED`, zero `FAILED`, zero `SKIPPED`, `PYTEST_EXIT_CODE=0`, `168_A9_TEST_EXIT_CODE=0`, and final `VRES_PERSONAL_168_A9_WINDOWS_SELECTED_TEST_COMPLETE` marker. Selected offline acceptance applies only to this exact source SHA, not broader Windows integration, independent Claude code security review, installed release, or physical isolation proof.

- Branch `feature/168-personal-adoption-preview-a9-20261030`.
- Validated HEAD **5e2479648f836417b5719d1eae0c983dd5d4b367**.
- Validated tree **f46cfe14f448084a488b4a8315481b3196be534f**.
- Direct parent **f197ca9997b86bccb0fcb9bf6009dbc534d43391**, accepted A8; tree `d282d7b6ad42470857e0b4f73a6f865478e1133c`.
- New detached worktree `C:\Projects\Vres-ChatGPT-Review-168-Prelaunch-Preview-A9-20261030`. Return prompt after script remained at PT2D because the test script restored the previous working directory; does not mean A9 tests ran there.
- Original P2 anchor `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` exact HEAD `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`, clean.
- Prior selected-tested A8 worktree `C:\Projects\Vres-ChatGPT-Review-168-Plan-Findings-A8-20261030`, parent HEAD/tree and clean.

## 2. Source change identity

Source branch remote and fetched SHA were exact and agreed with GitHub. Fresh detached HEAD/tree/sole parent, **24 protected Git blob identities pre- and post-test**, allowlisted exact three paths, `git diff --check` and worktree-clean checks all reported PASS.

Exactly three changed paths relative to A8, independently confirmed by GitHub one-ahead/zero-behind compare:
1. M `src/vres_os/cli.py` blob `a70b843bc9b535231f1992e2f3bbefafc4ac7ac3` — adds `vres project preview` operator command.
2. A `src/vres_os/project_preview.py` blob `92a3013acea472ecb26a03d7a7be41bd88b4981e` — stateless, safe-metadata bounded offline classification reusing established inventory and architecture audit; never loads or persists Vres adoption state; refuses >65536-byte report, no raw secret content/file hashes, and declares no activation/project/state writes.
3. A `tests/test_project_preview.py` blob `697669ee7472806bc639b14d98fec78368dfa6f5` — eleven new synthetic regression functions.

## 3. Actual selected test evidence

The one guarded Python3.12 command with `-B -m pytest -q -rA -p no:cacheprovider` selected exactly the eleven A9 preview tests and six inherited A8/A7/A1/P2-D cases.

All **17** appeared individually as `PASSED`:
- New: fresh project deterministic no-create, one-file fresh nonactivation, established source no-Claude plan hold, executable legacy hook does not run, small legacy KEEP/DROP, sensitive input not echoed, unknown audit limitation denies fresh classification, prior adoption state untouched, oversized report refuses, CLI preview no setup/DB/model or state create, incomplete inventory refuses.
- Inherited: material findings map to prior A8 plan, no-Claude held review, read-only CLI findings, A7 held-legacy plan template, established-project architecture gate, historical P2-D existing-legacy inventory.

In-process protected AppData fence reported **unexpected refusals=0** against current-user local/roaming VresOS paths with disposable temporary test directory and `integration_opt_in=False`. Test environment reported `PYTEST_PLUGIN_AUTOLOAD=DISABLED`, process DB/PG/integration variables isolated, exit code 0, `PROCESS_ENVIRONMENT_RESTORED`. Post-test exact HEAD/tree and **all 24 pinned blobs**, fresh A9 and prior A8 worktrees clean; exit 0 and final completion marker.

These controls are scoped safeguards, not direct independent proof that no physical TCP packets, filesystem hooks or actual SQL connections occurred.

## 4. Product and incident limits

A9 is a source-level, non-authorizing **prelaunch preview**. It does not install or activate Vres, run `start`, modify the real legacy project, inspect a current installed state, modify global Claude/PRISM configuration, copy credential values, choose a new Chairman model, or issue Fable/high protected consent/validation. A follow-up actual adoption must re-inventory and re-audit, and remain within #168 activation holds.

**LIVE_SCHEMA_048_INCIDENT=OPEN**: no PostgreSQL access even SELECT, including via Vres CLI, tasks, MCP, hook paths, bootstrap, health, migrations or recovery. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**: seven earlier native Claude Code read/grep calls triggered automatic refused DB routes. Hook-R1 34 selected Windows PASS was source-only, not installed/global/managed/lifecycle clearance. An earlier Claude Code `--safe-mode` UI launched from wrong PT2D worktree displayed v2.1.312 Opus 5.5 / Max, but did not constitute A7/A8/A9 independent review, positive native hook clearance, or Vres Chairman Opus/medium installation. Independent A9 Claude review NOT_RUN.

All previous exact-P2/PT1/PT2A-D/Hook-R1/#168 A1-A8 test acceptances and rejected/skip evidence remain preserved. P0-P3 personal governance, positive independent F1 issuer and protected Fable/high are not waived. Product main, real user installation, credentials, external effects, actual Visual Studio legacy project acceptance and go-live are unchanged.

## 5. Next engineering and operating cadence

Continue under [canonical current index](VRES-CHATGPT-CONTINUITY-INDEX.md) and [full-scope ChatGPT-led roadmap](../roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md), preserving full V-01..V-42 register, #165–170, #174, E7/E8, #166 global Claude/PRISM onboarding, #167 current-user Data Source Registry, #169 Visual Studio physical acceptance, #170 personal readiness.

ChatGPT selects one useful **offline** increment from A9 accepted parent, makes a separate non-merged GitHub source commit with regression tests, and supplies the operator ONE complete, SHA-pinned, fail-fast PowerShell code block for a fresh detached worktree and selected offline tests. Operator returns the *complete* console. ChatGPT reviews failure/acceptance truthfully and updates docs only afterward. Do not split one executable script into fragments, do not repeat the previous accepted suite without a changed dependency, and do not run native Claude Code review while the hook incident remains unproven safe.
