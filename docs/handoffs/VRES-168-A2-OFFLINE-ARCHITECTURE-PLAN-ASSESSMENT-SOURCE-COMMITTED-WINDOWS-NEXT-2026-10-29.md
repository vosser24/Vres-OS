# Vres-OS PERSONAL #168 A2 — offline audit-bound architecture plan assessment source committed; one guarded Windows test NEXT

**Date:** 2026-10-29 Europe/Athens. **Repository:** vosser24/Vres-OS.
**CURRENT:** 168_A1_R1_WINDOWS_SELECTED_88_PASS_EXIT0 / 168_A2_SOURCE_COMMITTED / A2_WINDOWS_TEST_NOT_RUN / A2_INDEPENDENT_CLAUDE_STATIC_NOT_RUN / A2_NO_PROTECTED_FABLE_CALL / NO_INSTALLED_USER_WRITE / DB_AND_HOOK_INCIDENTS_OPEN.

## 0. Direct predecessor is Windows accepted, not installation

The exact parent source feature/168-personal-established-project-architecture-gate-20261029 HEAD **fa54b68cd8bfdf86c9de6782040858957976dd02**, tree **5f57c7d9b06d45ba18c14369409d59461d508e10**, was tested on the user's Windows host: **88 DISTINCT named tests PASSED / zero failures / PYTEST_EXIT_CODE=0 / final VRES_PERSONAL_168_R1_WINDOWS_SELECTED_TEST_COMPLETE**, with 13 protected Git objects pre/post and disposable AppData fixture unexpected refusals=0. The original user upload's 14,003 UTF-8 CRLF bytes are preserved as Git blob **88603126de2669ee95a44edf9ffb6d56609990c2**, raw SHA256 **77e2dff55579fd7a01e122ca10ae9d70491e9cb5943de1e56ab8bb437d1c9528**. See [R1 Windows PASS handoff](VRES-168-A1-R1-WINDOWS-88-PASS-EXIT0-AND-NEXT-OFFLINE-PROJECT-ADOPTION-STAGE-2026-10-29.md). Original rejected A1 84 PASS/2 FAIL/exit1 preserved separately, not retroactively accepted. R1 remains selected Windows accepted at that SHA and independent Claude source review NOT_RUN.

## 1. Exact new A2 source and behavior

New source branch **feature/168-personal-architecture-plan-contract-20261029**.
GitHub HEAD **3ce27dd2fa46b9b2f3bb921c92e953926bcf8c8d**.
Tree **76fa41d6561fc26454eb46149f4ddabd308d5f36**.
Sole parent **fa54b68cd8bfdf86c9de6782040858957976dd02**.
Nonforced expected-old GitHub branch update, commit/tree/parent/ref readback and compare EXACTLY ONE commit ahead, zero behind, TWO changed paths:
- M src/vres_os/project_adoption.py, parent blob **824389d8f2fac39d4c2f4b1c3f2f6c8ad990f68c**, new blob **7747d2ea5891debda173fa2b5d71bc0699303304**; append-only public assess_alignment_plan function, existing P2-D and A1 code unchanged.
- A tests/test_project_adoption_alignment.py, new blob **1d1eeafb597e5e6a5e6385c3f3dc7ddd58586b0b**, 271 lines, THIRTEEN new synthetic test functions.

New **assess_alignment_plan(project, plan, data_root=...)** is an offline-only, strictly non-authorizing proposal-assessment method:
- Requires an existing ordinary Vres adoption state directory and exactly architecture_review_required state, with matching project key and original project root; no new state directory is created.
- Refuses any interrupted adoption journal, incomplete/unknown/static source-audit limitation, changed recorded structural audit digest/profiles, or a project that is no longer established.
- Reuses accepted read-only architecture_governance.audit_project and architecture_plan.check_alignment_plan; bounds supplied canonical JSON plan to 65,536 bytes, at most 64 tranches and 128 exceptions, treats recursion/serialization and invalid nested fields as contract invalid.
- Returns current structural audit digest and explicit digest-scope warning, proposed plan digest (if valid), bounded validation errors, independent required Fable/high identity and result PLAN_READY_FOR_PROTECTED_VALIDATION only for a syntactically complete contract, else PLAN_CONTRACT_INVALID. Regardless, **activation_allowed=False**, **project_write_permitted=False**, **protected_validation_required=True**. Does not change stored adoption state, execute project code, contact Vres DB/credentials/MCP, call any model or grant user authorization.
- Digest is the ACCEPTED existing #174 STRUCTURAL findings digest, not a cryptographic hash of all source file bytes, and no physical model identity/protected endorsement is inferred. No CLI exposure, plan persistence, protected approval, new installed file, go-live or actual project activation is claimed.

The 13 new authored tests use disposable synthetic roots and inspect: valid plan with no activation and no project/state changes; deterministic repeat; stale plan audit digest; forged claimed Fable approval; changed source since snapshot; missing state creates nothing; fresh active source cannot misuse review; cross-project same-key root mismatch; malformed/cyclic/oversized plan; invalid nested exception; new syntax-unavailable source; unknown new limitation; interrupted journal. All rely on existing #168 A1 R1 / #174 code; A2 has NOT been Windows executed.

## 2. Next ONE guarded Windows operator step

The complete exact SHA-pinned script is [A2 166-line guarded Windows test](VRES-168-A2-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-29.ps1), Git blob **17b636981a56b544f6b9743fd36d278203b5366a**. **Always display the COMPLETE literal block INLINE in ChatGPT, not merely link a file.**

Script uses:
- Original anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 exact HEAD **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c** clean.
- Previous Windows-accepted A1 R1 detached checkout C:\Projects\Vres-ChatGPT-Review-168-Architecture-Gate-R1-20261029 at exact parent **fa54b68cd8bfdf86c9de6782040858957976dd02**, tree **5f57c7d9b06d45ba18c14369409d59461d508e10**, clean. DO NOT reset, overwrite or rerun R1 tests.
- NEW detached checkout C:\Projects\Vres-ChatGPT-Review-168-Plan-Assessment-20261029 must not exist. Check official GitHub origin, exact remote/fetched A2 HEAD, create detached worktree, assert new HEAD/tree/sole parent/14 protected Git blobs and exact one M source + one A focused new test, diff --check, clean.
- ONE Python3.12 py -3.12 -B -m pytest -q -rA -p no:cacheprovider, with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, process-only PG/DB/integration vars clear and finally restored, disposable protected AppData conftest. Only new tests/test_project_adoption_alignment.py plus FOUR individually named legacy regression cases: established-source architecture hold and fresh-one-file scaffold from tests/test_project_adoption_architecture_gate.py, valid plan protected Fable gate and stale audit digest denial from tests/test_architecture_governance.py. No full already-passed 88-case test rerun.
- Demand printed all individually PASSED/FAILED/ERROR, actual immediate PYTEST_EXIT_CODE, PROCESS_ENVIRONMENT_RESTORED, posttest HEAD/tree/14 blobs, both new A2 and previous R1 checkout clean, and A2 exit. Only if all PASS and exit0 will final **VRES_PERSONAL_168_A2_WINDOWS_SELECTED_TEST_COMPLETE** appear. STOP/ABORT or missing marker means NO Windows acceptance; do not run fragments after a STOP. User returns entire stdout/stderr console.

## 3. Preserved program scope and physical holds

This is ongoing **V-30/#168** practical project adoption engineering from [full V-01..V-42 register](../roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md) and [October 22 ChatGPT-led plan](../roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md), not mere model-policy documentation. Major #168 gaps still include real architecture plan creation, independent protected Fable/high approval with authentic host identity, authorized activation/rollback and legacy-with-Claude project alignment; #166 current-user Claude/PRISM adoption, #167 data-source reuse, E7/E8 learning, #169 Visual Studio legacy project, #170 pilot/go-live. Do not mislabel a pure plan check as completing #168.

**LIVE_SCHEMA_048_INCIDENT=OPEN — ABSOLUTELY NO PostgreSQL contact even SELECT**, direct or via Vres MCP/CLI/tasks/hooks/bootstrap/doctor/health/F2/recovery. **HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**, historical PT1 Claude read-only reviewer seven automatic posttool DB-routing attempts all REFUSED. Hook-R1 source matcher fix selected 34 Windows PASS but installed/global/lifecycle hooks not installed or verified; do NOT start normal Claude Code reviewer. Original P2 installed Chairman last observed Sonnet/high, requested Opus/medium UNINSTALLED, effective physical model unknown and strict F1 protected independent positive authority BLOCKED. PERSONAL risk tiers P0/P1/P2/P3, protected Fable/high arbiter/validator and worker model pins, secure current-user credential handles, project isolation, full E7/PA/F2/production holds remain.

**Method:** ChatGPT is source architect, author and GitHub committer. User runs ONE complete atomic exact SHA-pinned guarded Windows PowerShell script, returns complete original output, ChatGPT evaluates and corrects only genuine failures in a new SHA and seals meaningful docs-only handoffs. Independent Claude Code via existing subscription only once zero automatic prohibited DB attempts is demonstrated; no web Chat, API-key/tier preflight diversion. Do not preclaim A2 PASS or ask to reinstall Vres/Claude.
