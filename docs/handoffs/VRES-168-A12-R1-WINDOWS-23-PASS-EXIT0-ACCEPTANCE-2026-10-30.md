# Vres-OS PERSONAL #168 — A12 R1 23-pass Windows selected ACCEPTED; original A12 rejected evidence preserved

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS. **Evidence:** full-looking original console pasted by user in ChatGPT; not separately SHA-256 attested Windows raw stdout bytes or network packet logs.

## Exact source and disposition

**A12_R1_WINDOWS_SELECTED_ACCEPTED** on `feature/168-personal-adoption-record-read-fence-a12-20261030`, corrected R1 HEAD **80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966**, Git tree **259e507b79dd7a2034ba9c9350f943665df13fbe**. R1 direct parent `6730da195ba3d4e4bb62841e7c03ee11ec0e004a`, whose sole parent is **ORIGINAL A12 REJECTED** `345a568b551ac23183c54f10611335adee903b96`, tree `0851934f4a79e297e136d512f6ae6d1e6f707e2d`, itself descended from accepted A11 `d58db1b5cea0c74040f1d25a219e80e0180c8efd`. Compare original rejected A12 to corrected R1 = 2 commits ahead, 0 behind and net exactly two M paths: `src/vres_os/project_adoption.py` blob **3fe1680ece8676bd743337f37b20ae50df611089**, `tests/test_project_adoption_record_read_fence.py` blob **b0a2fae7875049a37a3420e5b3f63905229c9f75**.

**Original A12 Windows result stays REJECTED:** exact rejected SHA `345a568...`, **18 individually named PASS, 1 FAIL, exit1**, `test_deeply_nested_json_refused_without_unbounded_parser_recursion` did not raise on 1,500 deep arrays; preflight/27 pre+post blob integrity and environment restoration passed. Do NOT rewrite original result or delete the original failed but clean Windows checkout.

## R1 operator preflight and Windows results

User executed the exact one-block SHA/27-blob guarded PowerShell script `docs/handoffs/VRES-168-A12-R1-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1`, immutable final Git blob **a3422e55388271dc87bcda8bbe34a88735c1d4db**. The ordinary Windows PowerShell output reported all these facts explicitly:

- Original P2 `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` at `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c` clean; accepted A11 `C:\Projects\Vres-ChatGPT-Review-168-Decision-Integrity-A11-20261030` exact SHA/tree clean; original rejected A12 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030` exact rejected SHA/tree clean.
- Official GitHub origin, exact remote and fetched R1 branch HEAD, new fresh detached `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-R1-20261030` at R1 exact SHA/tree, sole direct parent and checked full intermediate->rejected->accepted A11 ancestry. All passed.
- All **27 individually listed protected Git blobs** before and after tests exact PASS; net two M file allowlist versus original rejected A12, `git diff --check` and all worktrees clean; `VRES_PERSONAL_168_A12_R1_PREFLIGHT_PASS`.
- One Python3.12 process-isolated `-B -m pytest -q -rA -p no:cacheprovider` selected all **16 record-read tests + seven P2-D/A11/A7 compatibility** functions: **23 distinct PASSED, ZERO failed/errors/skips**, including the 1,500-deep formerly rejected case, exactly-128-level accepted, 129-level denied, escaped quotes/brackets ignored, mismatched delimiters denied.
- `PYTEST_PLUGIN_AUTOLOAD=DISABLED`, process DB/PG/integration environment variables isolated and finally restored, disposable AppData fence `unexpected refusals=0`, `integration_opt_in=False`; `PYTEST_EXIT_CODE=0`, `PASS: PROCESS_ENVIRONMENT_RESTORED`.
- Posttest R1 exact SHA/tree and 27 blobs PASS, R1 clean, original rejected A12 preserved clean, previously accepted A11 unchanged clean, `168_A12_R1_TEST_EXIT_CODE=0`, final `VRES_PERSONAL_168_A12_R1_WINDOWS_SELECTED_TEST_COMPLETE`. PowerShell returned to PT2D due to `Pop-Location`; tests actually ran inside new R1 worktree.

## Accepted functional scope and limitations

A12 R1 enforces 2MiB bounded saved-adoption JSON read, ordinary linked/junction-denial at file and immediate parent, pre/post file descriptor identity and no-follow where available, UTF-8/JSON refusal, and deterministic maximum **128 structural nested levels** before parsing, ignoring quoted and escaped delimiters. Retains A11 stored KEEP/DROP option/path/hash integrity. It is NOT a cryptographic trusted issuer, complete protection against all filesystem ancestor races, installed release acceptance or real project activation approval. Test fixture/process DB isolation not an independent direct TCP packet/SQL traffic trace.

## Binding incidents and full-scope continuation

**LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT**, directly or via Vres CLI/MCP/hooks/bootstrap/doctor/migration/F2/recovery. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** seven historical native Claude Code Read/Grep automatic posttool DB-routing attempts refused; Hook-R1 selected Windows 34-pass source alone does not clear installed/global/lifecycle/managed hook behavior. Earlier accidentally started Claude `--safe-mode` from PT2D not a security review, native hook clearance or Vres Chairman model change. **Independent native Claude A12 R1 security review NOT_RUN**; original installed P2 Chairman Sonnet/high last observed, requested Vres Opus/medium not installed. F1 positive issuer and protected Fable/high validation are still blocked. No installed Vres/Claude/PRISM, credential, real project, live DB, product main, PR, merge or go-live change.

Carry forward PERSONAL P0–P3, PT1/PT2A–D, Hook-R1, #168 A1–A11 accept/reject/skip truth, original rejected A12 18/1, entire V-01..V-42, #165–170, #174, E7/E8, #166 global Claude/PRISM, #167 Data Source Registry, #169 Visual Studio real-project and #170 local readiness. Continue smallest bounded offline source increment on A12 R1 exact HEAD, fresh GitHub feature branch with tests -> ONE full standalone PowerShell test block for SHA-pinned detached Windows checkout -> user entire console -> targeted acceptance/repair -> docs seal. No normal native Claude Code review until independently clear no-hook boundary.
