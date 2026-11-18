# 2026-11-18 — Independent #185 review request: CURRENT original Claude CLI/FastMCP R-7 lifecycle persistence

**REQUEST ONLY. No independent reviewer/acceptance, no runtime tests, no operational authority.**

## Freshly verify the exact code and issue yourself

- GitHub `vosser24/Vres-OS` ID `1368577038`, account `vosser24` ID `62554356`, app installation `85535881`.
- Source branch `feature/personal-w4-original-task-lifecycle-persistence-r7-20261118`, [commit `4a901c429dfad1e74d093de5750af4c48dc16da0`](https://github.com/vosser24/Vres-OS/commit/4a901c429dfad1e74d093de5750af4c48dc16da0), TREE `f85692f4d7e47d339eced4b4bb40857a9b44f36f`, sole PARENT R-6 `85bbdec64d25478ecff1a4c6ecee90db85a1d135`. Raw Git parent/tree, remote ref, exact changed-file blobs and direct comparison 1 ahead/0 behind were read back.
- Exact changed paths: `src/vres_os/task_lifecycle.py` Git blob `102b559576e423644cffdf5a0d4cb7cc3fe8aae5`; `tests/test_task_lifecycle_persistence_redaction.py` blob `dbb7bb465e5d1fcedc17f8bc172e0855a3017deb`; `docs/architecture/VRES-W4-ORIGINAL-TASK-LIFECYCLE-PERSISTENCE-R7-2026-11-18.md` blob `aa0ddec0dbb3740a3ac8f8e46a7fa44104c79053`.
- Main held `9a8acc5d464b96432a93cb95daa9581412fb07ee`; R13 held `bcf62460d68caebfdbd0e838d44c5997992c5fbc`. R-7 250 ahead / 0 behind main, diverged R13 141 ahead / 13 behind, no merge.
- **Read the ENTIRE [#185 issue](https://github.com/vosser24/Vres-OS/issues/185) body and ALL comments (eight observed at publication; recheck count) plus R-6 prior review request, R-2..R-5 source, original CLI/FastMCP/Chairman/Repository, real session task_resume, D1–D4, protected R13 original stage/release, original install.ps1/update.ps1, V-01..V-42/M0..M8/W4 roadmaps.** Issue/comments themselves are requests, not verdicts.

## Independent reviewer questions with exact source targets

1. `src/vres_os/task_lifecycle.py` original `transition_task_status`: R-6 predecessor used display-only `redact()` on status reason then stored `TASK_STATUS_CHANGED` event JSON; `src/vres_os/redaction.py` KV regex may mask only the prefix of `password=abc,def`. Does R-7 strict `redact_for_persistence()` suppress the full unsafe field in event AND outbound result without breaking clean status/cancel semantics? Evaluate over-redaction of legitimate lifecycle reasons.
2. Does importing/reusing ORIGINAL `Repository._persist_identity_unmodified` in task lifecycle create any import/cycle/caller mismatch? Confirm tainted task_key and provider_session_id cannot reach cancellation instruction provenance, SQL/event rows, exceptions or outbound status; confirm no accidental key masking or changed join semantics.
3. Are there additional direct persistence routes outside Repository's strict sanitizer? In `session_prompts.py` lines ~126–163 `_stage_entry` calls DISPLAY `redact()` for user text/tool-use id/question before `vres.stage_user_input`; check bounded, correctly authorised, secret-safe stage/commit/replay without losing current-user cancel authority. In `session_lifecycle.py` ~138–239 and ~241–326, reused historical task/session identifiers enter direct event JSON. Inventory other original direct SQL, logs/errors, outbound CLI/FastMCP and historical rows. **Do not misrepresent as a proven live leak.**
4. Does R-6 explicit session-bound `resume_context` genuinely use `bind_session`'s one transaction for binding + focus with rollback and concurrent selections? Check real original Claude IDs, session ownership and project isolation. R-7 did not change R-6 binding.
5. Independent first-FULL release assessment: exact pre-execution source/publisher/SHA-256/Python/toolchain and wheel closure, original D1–D4, R13 refusal and original `release_artifact.stage()` alternate path, inert 248-file source ZIP ≠ executable first-FULL, original default-NO per-package installer offers, Windows NTFS ACL/ADS/reparse/hardlink/case/race/recovery and true full V-01..V-42 scope. No enterprise IAM/second GUI proposal.

## Exact independent deliverable

- **THREAT_MODEL: ACCEPT / REVISE / REJECT.**
- **RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.**
- **OPERATIONS:** explicit **PERMITTED / CONDITIONAL / BLOCKED** for GitHub read/authoring, source Python/AST/compile/pytest, Windows/POSIX/Git/downloads, source checkout, installer/preflight, original release/staging, protected installed P2, credentials/profile, native Claude/FastMCP/hooks, PostgreSQL even SELECT, F1/Fable, real legacy/PRISM/TASK-DAY-01, main/R13 merges, full real UAT, rollback.

Require distinct attributable reviewer identity, path/line and commit evidence, P0/P1/P2/P3 findings with minimal remedies, actual PASS/FAIL/NOT_RUN separately, residual risks and scope conditions. Do not substitute original author, unsigned external AI report or self-review for independent acceptance. A favorable static review alone grants no operational permission.

**Test provenance:** current R-7 R-6/R-5 synthetic tests AUTHORED NOT_RUN; CURRENT Python/AST/compile/pytest/PowerShell/Windows/native host/PostgreSQL/UAT NOT_RUN. Historical 732/732 PASS and 407/407 compile ONLY old source `9e2b538b` (nine child cases deselected, three psycopg modules not collected, earlier 727/730 with three fixture FAIL). DO NOT transfer historical PASS.

**ABSOLUTE HOLDS:** `LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT**; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: **NO ordinary native Claude Code or installed FastMCP/hooks**. Trusted F1/Fable positive authority not granted; P3/L2/R13/main, installed Windows P2, credentials/profile/real legacy/PRISM/TASK-DAY-01, Windows installation/update/recovery/UAT and destructive rollback all HELD. No reviewer has permission to run DB/host/install/OS commands.
