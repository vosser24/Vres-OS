# Vres-OS PERSONAL #168 A15 — guarded Windows selected 22 PASS / exit 0 ACCEPTED

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS. **Evidence:** complete-looking Windows PowerShell output pasted by operator directly into ChatGPT; not separately SHA256-attested original Windows CRLF stdout bytes, independent physical SQL/network capture or native Claude Code security signoff.

## SHA-specific selected Windows disposition

**A15_WINDOWS_SELECTED_ACCEPTED**: exactly **22 distinct tests PASSED**, zero FAILED/SKIPPED, `PYTEST_EXIT_CODE=0`, `168_A15_TEST_EXIT_CODE=0`, final `VRES_PERSONAL_168_A15_WINDOWS_SELECTED_TEST_COMPLETE`.

- Source branch: `feature/168-personal-adoption-schema-type-a15-20261030`.
- Windows validated HEAD: **9d63044012e59663fbeb9448a08e9aabae5dbe7d**.
- Git tree: **46f6e00d6bc5e8baa9c7eae4f57b3cd76b2b85d6**.
- Sole Windows accepted A14 parent: **06fc9ddb488f7aa7ef1f980f0bfbe59b3a29b0fc**, tree **bd19a0237b4889553c974663e08ac0ada832eab4**. GitHub comparison independently verified one-ahead/zero-behind, exactly two file changes: M `src/vres_os/project_adoption.py` blob **a2710d1812e154907c55ca137e5dbe2ee16cd175**, A `tests/test_project_adoption_state_schema_types.py` blob **2f7eb491d10ca6553dc0f1291738c5e053939bf9**.

## Windows console preflight, selected tests and postconditions

Operator ran canonical one-atomic SHA-pinned PowerShell `docs/handoffs/VRES-168-A15-GUARDED-WINDOWS-SELECTED-TEST-NEXT-2026-10-30.ps1`, Git blob **67c95b802b335640591dc9dc5a0a1b32c100ad79**. It reported:
- Original P2 anchor `C:\Projects\Vres-P2F-Postinstall-Hardening-20261022` exact `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`, clean.
- Previously accepted A13 R1 `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-R1-20261030` exact SHA/tree clean; previously accepted A14 `C:\Projects\Vres-ChatGPT-Review-168-State-Root-Binding-A14-20261030` exact SHA/tree clean.
- Original rejected A12 `C:\Projects\Vres-ChatGPT-Review-168-Record-Read-A12-20261030` and rejected A13 `C:\Projects\Vres-ChatGPT-Review-168-Record-Ancestors-A13-20261030` exact rejected SHAs/trees clean.
- Official GitHub remote and fetched A15 exact HEAD, fresh detached checkout `C:\Projects\Vres-ChatGPT-Review-168-State-Schema-Types-A15-20261030` at exact HEAD/tree/sole parent and full checked ancestry.
- **30 individually protected Git blobs** before and after, exact M adoption source + A new regression tests allowlist, diff--check and clean, `VRES_PERSONAL_168_A15_PREFLIGHT_PASS`.

A single process-isolated `py -3.12 -B -m pytest -q -rA -p no:cacheprovider` selected **14 new A15 tests and eight inherited A14/A11/P2-D tests**, all **22 separately listed PASSED**. New tests covered real integer v1 acceptance, JSON true/false schema version denial despite Python `True == 1`, float 1.0/string/null/list/object/unknown version denials, malformed boolean/array/null state names, ordinary legacy idempotence, and no activation-authority prompt on invalid true version. Inherited tests preserved project-root/clone isolation, invalid state structure, older version and fresh project checks, small legacy synthetic activate/rollback and interrupted activation recovery.

`PYTEST_PLUGIN_AUTOLOAD=DISABLED`, process DB/PG/integration environment isolated, temporary protected AppData fence `unexpected refusals=0`, `integration_opt_in=False`, `PYTEST_EXIT_CODE=0`, `PASS: PROCESS_ENVIRONMENT_RESTORED`. Post-test SHA/tree and **all 30 pinned blobs** PASS, A15/accepted A13 R1/accepted A14/rejected original A12/rejected original A13 checkout clean and unchanged, `168_A15_TEST_EXIT_CODE=0` and full completion marker. The prompt returning to PT2D was normal working-directory restoration, not evidence the tests executed in PT2D.

## Functional contract and limitations

A15 corrects the A14 bool-version bypass with `type(record.get("version")) is int` plus exact version integer 1, and requires a `str` state value matching known `STATES`. It does not confer approval of all persisted fields, introduce cryptographic positive F1 authority, install Vres or grant any real legacy activation. The selected offline Windows gate is not a full suite, native Claude independent source review or physical no-PostgreSQL packet proof.

## Historical rejections and binding holds

**Original A12 REJECTED:** SHA `345a568b551ac23183c54f10611335adee903b96` Windows 18 PASSED/1 FAILED exit1 (deep JSON). **Original A13 REJECTED:** SHA `cdaa39aaa774cef88a4831bf6b157e380fbb69d9` Windows 28 PASSED/1 FAILED exit1 (parent-junction diagnostic string). Both worktrees are clean and preserved; corrected A12 R1 had 23 selected PASS; corrected A13 R1 had 32 selected PASS. A14 23 PASS remains accepted.

`LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT**, direct or via Vres CLI/MCP/hooks/bootstrap/migrations/doctor/F2/recovery. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: seven prior native Claude Read/Grep post-tool DB routes refused; 34 Hook-R1 selected Windows matcher PASS does not establish installed/global/managed/lifecycle hook clearance. Earlier accidental Claude `--safe-mode` UI in PT2D not an independent source review or Vres Chairman model change. A15 independent native Claude Code review NOT_RUN; F1 trusted positive issuer and protected Fable/high approval BLOCKED. No installed/global Vres/Claude/PRISM, credentials, real legacy project activation, product main/PR/merge or go-live action.

Preserve full V-01..V-42 roadmap, PERSONAL P0–P3, PT1/PT2A–D, Hook-R1, #168 A1–A15 accepted/rejected/skipped provenance, #165–170, #174, E7/E8, #166 global Claude/PRISM, #167 single-user Data Source Registry and reusable credentials, Visual Studio #169 and go-live #170. Continue only scoped source-only GitHub work on accepted A15 exact SHA, then one entire copy-paste PowerShell gate with SHA-pinned clean fresh detached Windows worktree and selected tests, full console review, docs seal. No native Claude while hook incident open.
