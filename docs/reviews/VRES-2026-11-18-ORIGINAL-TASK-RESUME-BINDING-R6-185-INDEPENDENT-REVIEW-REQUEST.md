# 2026-11-18 — CURRENT R-6 original task_resume + Repository independent #185 review request

**REVIEW REQUEST ONLY; NO REVIEWER ASSIGNED, NO THREE-PART VERDICT, NO TEST EXECUTION, NO HOST/DB/RELEASE PERMISSION.**

## Verify current source identity yourself

- Repository: https://github.com/vosser24/Vres-OS ID `1368577038`, authenticated account `vosser24` ID `62554356`, App installation `85535881`.
- R-6 dedicated source branch `feature/personal-w4-original-task-resume-binding-atomicity-r6-20261118`; HEAD `85bbdec64d25478ecff1a4c6ecee90db85a1d135`; created tree `a6952c7bc65eb9f75324a85b60b938d5d6fac0ce`; sole specified parent R-5 `f70897ea1cf82d5cb7c5f0b701efee859a03dc5a`; [source commit](https://github.com/vosser24/Vres-OS/commit/85bbdec64d25478ecff1a4c6ecee90db85a1d135).
- Exact R-5→R-6 diff: 1 ahead, 0 behind, 3 paths: `src/vres_os/repository.py` blob `783873d4120fc3e21714c6a75fe24336c90126a9`, `tests/test_repository_persistence_redaction.py` blob `9e806ed7fb4ab522da86588cd0a8aad9a8fe2c7b`, `docs/architecture/VRES-W4-ORIGINAL-TASK-RESUME-BINDING-ATOMICITY-R6-2026-11-18.md` blob `d235df3c0ae7e7d4679e261245332f2d42b0d05b`.
- Remote source HEAD/three blobs and compare VERIFIED; GitHub connector raw TREE/PARENT commit-response readback unavailable in this chat, so independently verify before declaring raw metadata attestation. Main HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee` and protected R13 HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc` held.
- Read COMPLETE https://github.com/vosser24/Vres-OS/issues/185 body and all **eight** existing owner comments (recheck live count), R-2/R-3/R-4/R-5/R-6 source, D1–D4/release routes, all V-01..V-42/M0..M8/W4 roadmaps.

## Source-grounded questions requiring distinct attributable review

1. Does R-6 fix the R-5 `resume_context` pre-bind committed project-focus selection and genuinely rely on `bind_session`'s single transaction for explicit Claude session-bound resume? Review failed/wrong-project/completed/closed/invalid binding, concurrent focus, existing selected-task behavior, sessionless focus, rollback semantics, assumptions/caller behavior, and real original Claude task_resume integration. No live DB was read.
2. Are `_task_id` and `focus_task` credential-pattern guards and generic missing-task KeyError non-disclosure proportionate? Audit other Repository/read/write methods for raw structural IDs in exceptions, logs, event payloads, SQL parameters and outward views. Examine existing stored rows, false rejects of legitimate identifier strings and pre-connect partial side effects.
3. Review strict R-2/R-3/R-4/R-5 persistence sanitizer, credential-bearing structured JSON keys, project remote URL/name/root/branch, event/task/checkpoint/session fields, alternate direct SQL writers, session transitions and actual task result/history views. Distinguish observed source defects from proven live leaks.
4. Inspect test design but **do not claim PASS**. CURRENT R-6 Python/AST/compile/pytest all **NOT_RUN**, five new regressions AUTHORED NOT_RUN; PostgreSQL even SELECT PROHIBITED, native Claude/FastMCP/hooks HELD, Windows/PowerShell/install/UAT NOT_RUN.
5. Inspect original release/first-FULL trust (D1–D4, 248-file inert source ZIP vs actual executable companion, R13 refusal bypass via original stage(), 001–041 migrations vs 042+, original install.ps1/update.ps1 consent, independent Git/Python/Claude/wheel publisher/source provenance, Windows NTFS ACL/ADS/reparse/hardlink/case/race/recovery, historical 732/732 on OLD commit only). Avoid enterprise redesign.

## EXACT independent deliverable (not the author's own assessment)

- **THREAT_MODEL: ACCEPT / REVISE / REJECT.**
- **RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.**
- **OPERATIONS: explicit PERMITTED / CONDITIONAL / BLOCKED matrix** for GitHub read/authoring, source Python/AST/compile/pytest, Windows/POSIX/Git, source checkout, installer/preflight, original release/staging, installed P2, credentials/profile, native Claude/FastMCP/hooks, PostgreSQL even SELECT, F1/Fable, legacy/PRISM/TASK-DAY-01, main/R13 merge, full real UAT and rollback.

Each finding P0/P1/P2/P3 with source path/line/commit evidence, exact minimal correction, separately noted observed PASS/FAIL/NOT_RUN, reviewer attributable identity and accepted/residual risk. A positive narrow design opinion alone grants NO operational permission. Prior author-side feedback/owner comments and unsigned AI advisory cannot substitute for a distinct independent reviewer.

**ABSOLUTE HOLDS:** `LIVE_SCHEMA_048_INCIDENT=OPEN` — NO PostgreSQL even SELECT; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — NO native Claude or installed FastMCP/hooks. F1/Fable positive authority NOT_GRANTED; P3, Git L2, protected R13/main, installed P2, credentials/profile, Windows install/recovery/UAT, real PRISM/legacy and TASK-DAY-01 all HELD. Reviewer read-only; no command, package, DB query, native host or installation authorized by this request.
